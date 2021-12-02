from networkx.algorithms.shortest_paths.dense import floyd_warshall
from src.SrlgDisjointSolver import SrlgDisjointSolver

from tkinter import *
import logging
import copy
import threading
from time import sleep
from src.util.HelperFunctions import path_to_edgeset

log = logging.getLogger(__name__)

class SolverGUI(Tk):
    
    WIDTH = 1200
    HEIGHT =800
    SM_HEIGHT = 30
    MARGIN = 10
    CIRCLE = 2
    HIGHLIGHT = 10
    LINEW = 1

    def __init__(self, solver: SrlgDisjointSolver) -> None:
        super(SolverGUI, self).__init__()
        
        #Set up solver
        self._solver = solver
        self._solver.gui = self


        # threading
        self.threadblocker = threading.Event()
        self.threadblocker.clear()  # Lower flag right away 
        self.mainthread = threading.Thread(target=self._solver.solve)


        self._solution = None
        self.g = None
        self.init_drawing_graph()

        self.init_gui()
        

    #
    # GUI SETUP
    #
    def init_gui(self):
        self.title("SLRG-disjoint solver GUI")
        self.minsize(SolverGUI.WIDTH ,SolverGUI.HEIGHT)

        # FRAME 1 - for drawing 

        self.frame1 = Frame(master=self, width=SolverGUI.WIDTH, height=SolverGUI.HEIGHT - SolverGUI.SM_HEIGHT, bg="red")
        self.frame1.pack()


        self.canvas = Canvas(master=self.frame1, width=SolverGUI.WIDTH, height=SolverGUI.HEIGHT - SolverGUI.SM_HEIGHT, bg="gray")
        self.canvas.pack()
        self.update_canvas()

        self.frame2 = Frame(master=self, width=SolverGUI.WIDTH, height=SolverGUI.SM_HEIGHT, bg="gray")
        self.frame2.pack()

        self.btn_solve = Button(master=self.frame2, text='Solve', command=self.eh_solve)
        self.btn_solve.pack(side=LEFT)

        self.btn_step = Button(master=self.frame2, text='Step', command=self.eh_step)
        self.btn_step.pack(side=LEFT)

        #self.btn_minc = Button(master=self.frame2, text='Min-Cut', command=self.eh_minc)
        #self.btn_minc.pack(side=LEFT)
        
        #self.btn_s_b = Button(master=self.frame2, text='<', command=self.eh_sb)
        #self.btn_s_b.pack(side=LEFT)

        #self.btn_s_f = Button(master=self.frame2, text='>', command=self.eh_sf)
        #self.btn_s_f.pack(side=LEFT)


    #
    #   Graph Drawing
    #

    def init_drawing_graph(self):
        def scale_graph():
            g = copy.deepcopy(self._solver.jsg)

            # calculate bounding box infomartion TODO: migrate to other function
            x_min = min((n['coords'][0] for n in g['nodes']))
            y_min = min((n['coords'][1] for n in g['nodes']))
            x_max = max((n['coords'][0] for n in g['nodes']))
            y_max = max((n['coords'][1] for n in g['nodes']))

            # calculate scale according to canvas w/o margin
            canvas_width = SolverGUI.WIDTH - 2 * SolverGUI.MARGIN
            canvas_height = SolverGUI.HEIGHT - SolverGUI.SM_HEIGHT - 2 * SolverGUI.MARGIN

            w_r = canvas_width / abs(x_max - x_min)
            h_r = canvas_height / abs(y_max - y_min)
            scale = min(w_r, h_r)

            # modify coordinates:
            # min x & y should be at 0, flip y coordinates (mirror to X axis)
            # scale them to marginless canvas keeping integer values, add margin
            for n in g['nodes']:
                n['coords'] = [
                    int((n['coords'][0] - x_min) * scale) + SolverGUI.MARGIN,
                    int((y_max - n['coords'][1]) * scale) + SolverGUI.MARGIN,
                ] 
            
            return g
        g = scale_graph()

        def find_coords(index):
            for n in g['nodes']:
                if n['id'] == index:
                    return n['coords']
            return None

        # add edge coords

        for e in g['edges']:
            e['cf'] = find_coords(e['from'])
            e['ct'] = find_coords(e['to'])

        self.g = g

    
    def find_coords(self, index):
            for n in self.g['nodes']:
                if n['id'] == index:
                    return n['coords']
            return None

    def draw_path(self, path, color='red', wid = None, dash=None):
        if wid is None:
            wid = SolverGUI.LINEW
        for i in range(len(path) - 1):
            ca = self.find_coords(path[i])
            cb = self.find_coords(path[i + 1])
            if dash is not None:
                self.canvas.create_line(ca[0], ca[1], cb[0], cb[1], fill=color, arrow = LAST, width=wid, dash=dash)
            else: 
                self.canvas.create_line(ca[0], ca[1], cb[0], cb[1], fill=color, arrow = LAST, width=wid)

    def update_canvas(self):
        self.canvas.delete('all')

        # draw the edges  
        for e in self.g['edges']:
            ca = e['cf']
            cb = e['ct']
            self.canvas.create_line(ca[0], ca[1], cb[0], cb[1], fill='black', width=SolverGUI.LINEW)
           
        
        
        # draw edges from pathq.

        if self._solution is None:

            # Get oldest path's common SLRG edges and highlight them 
            edges_to_highlight = set().union(*[self._solver.PG.S[edge] for edge in path_to_edgeset(self._solver.oldestpath)])   # All the edges that are in a common SLRG with at least on edge in oldest

            for e in edges_to_highlight:
                u, v = e.unpack()
                cu = self.find_coords(u)
                cv = self.find_coords(v)
                self.canvas.create_line(cu[0], cu[1], cv[0], cv[1], fill='yellow', width=SolverGUI.HIGHLIGHT)


            for path in self._solver.pathqueue:
                self.draw_path(path)

            # draw oldest path with purple:
            self.draw_path(self._solver.oldestpath, 'purple', SolverGUI.LINEW * 2)

            # draw newest path with purple dashes:
            self.draw_path(self._solver.newestpath, 'lightblue', SolverGUI.LINEW * 2)

            # draw novel try path with yellow dashes:
            self.draw_path(self._solver.novelpath, 'lightgreen', SolverGUI.LINEW * 2)

        else:
        # IF soultion is set, drwa edges as well
            for path in self._solution:
                self.draw_path(path, wid= SolverGUI.LINEW * 2)
        
        # draw the nodes
        for n in self.g['nodes']:

            self.canvas.create_oval(
                n['coords'][0] - SolverGUI.CIRCLE,
                n['coords'][1] - SolverGUI.CIRCLE,
                n['coords'][0] + SolverGUI.CIRCLE,
                n['coords'][1] + SolverGUI.CIRCLE,
                fill='white'
            )
            #self.canvas.create_text(n['coords'][0], n['coords'][1], text=n['id'])

            
    
        self.canvas.pack()

    #
    # EVENT HANDLERS
    #

    def eh_solve(self):
        log.debug("BTN 'Solve' Clicked")
        self.mainthread.start()     # Start thread
        self.threadblocker.set()    # Raise flag

    def eh_step(self):
        log.debug("BTN 'Step' Clicked")
        self.threadblocker.set()    # Raise Flag
        pass

    def eh_minc(self):
        log.debug("BTN 'Min-Cut' Clicked")
        pass

    def eh_sb(self):
        log.debug("BTN '<' Clicked")
        pass

    def eh_sf(self):
        log.debug("BTN '>' Clicked")
        pass


