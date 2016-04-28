from tkinter import *
from tkinter.ttk import *
from random import random, shuffle, choice
from math import *
from time import time, sleep
from threading import Thread
import time_profile
from bisect import insort, bisect_left

from SimpleMaths import linear_map
from animation import AnimatedValue


class EndOfChainError(Exception):
    pass


class MarkovNode():
    def __lt__(self, other):
        try:
            return self.value.__lt__(other.value)
        except AttributeError:
            return self.value.__lt__(other)

    def __init__(self, value, mode):
        '''
        Gets a Canvas object and places itself on the canvas.
        value is the tuple of the string values of the node.
        '''
        self.value = value
        self.destination_nodes = list()  # List of all node occurences. May contain duplicates.

        self.mode = mode

    # Information getting methods
    def get_seperator(self):
        if self.mode == 'Word':
            return " "
        elif self.mode == 'Character':
            return ""
        elif self.mode == 'Line':
            return "\n"
        else:
            print("ERROR - Unexpected Mode1")
            exit()

    def get_value_string(self):
        return self.get_seperator().join(self.value).replace(" ", "_").replace("\n", "\\n")

    def get_last_value(self, add_seperator=True):
        return self.value[-1] + self.get_seperator()

    def _unique_destinations(self):
        return list(set(self.destination_nodes))

    def _unique_destinations_with_occurences(self):
        return [(i, self.destination_nodes.count(i)) for i in self._unique_destinations()]

    def cache_sorted_unique_destination(self):
        if hasattr(self, "cached_sorted_unique_destination"):
            return
        self.cached_sorted_unique_destination = self._unique_destinations_with_occurences()
        self.cached_sorted_unique_destination.sort(key=lambda x: x[1])
        self.cached_sorted_unique_destination.reverse()
        try:
            self.max_connections = self.cached_sorted_unique_destination[0][1]
        except IndexError:
            self.max_connections = 0
        self.cached_sorted_unique_destination = [i[0] for i in self.cached_sorted_unique_destination]

    def sorted_unique_destinations(self):
        return self.cached_sorted_unique_destination

    def get_max_connections(self):
        return self.max_connections

    # Chain creation/jumping methods
    def connect(self, destination_node):
        '''
        Creates a new link from this node
        to the destination_node(also a MarkovNode).
        '''
        self.destination_nodes.append(destination_node)

    def select(self):
        '''
        Selects one of the connected nodes.
        '''
        try:
            return choice(self.destination_nodes)
        except IndexError:
            raise EndOfChainError


class MarkovDraw:
    active_color = "#FF0000"
    inactive_color = "#000000"
    line_color = "#808080"
    active_line_color = "#FF8080"
    text_font = "Ariel", 24, "bold"

    @staticmethod
    def change_font_size(size):
        MarkovDraw.text_font = MarkovDraw.text_font[0], size, MarkovDraw.text_font[2]

    def __init__(self, markov_node, canvas, x=random() * 300, y=random() * 300):
        self.node = markov_node

        self.coordinate = [x, y]

        self.animated_x = AnimatedValue(self.coordinate[0])
        self.animated_y = AnimatedValue(self.coordinate[1])

        self.canvas = canvas

        self.line_ids = dict()
        self.text_id = canvas.create_text(self.coordinate[0], self.coordinate[1],
                                          text=self.node.get_value_string(), fill=MarkovDraw.inactive_color,
                                          font=MarkovDraw.text_font)
        self.canvas.tag_raise(self.text_id)  # Place the text at the topmost stack

    def connections_to_width(self, num, mx):
        '''
        How thick should each line be, given the number of connections?
        '''
        global width_multiplier, max_connections_per_node
        # return num/max_connections_per_node*width_multiplier
        return num / mx * width_multiplier

    def draw_lines(self, targets):
        for destination_node in targets:  # create a new line
            self.line_ids[destination_node] = self.canvas.create_line(
                self.coordinate[0], self.coordinate[1],
                destination_node.coordinate[0], destination_node.coordinate[1], fill=MarkovDraw.line_color,
                width=self.connections_to_width(self.node.destination_nodes.count(destination_node.node),
                                                self.node.get_max_connections()))

            self.canvas.tag_lower(self.line_ids[destination_node])  # Place the line at the bottommost stack

    def max_connections(self):
        mx = 0
        for i in self.node.destination_nodes:
            n = self.node.destination_nodes.count(i)
            if n > mx:
                mx = n
        return mx

    def update(self, current_time):

        try:
            self.canvas
        except AttributeError:
            return  # Not yet drawn.
        x = int(self.animated_x.get_value(current_time))
        y = int(self.animated_y.get_value(current_time))
        dx = -self.coordinate[0] + x
        dy = -self.coordinate[1] + y
        if dx != 0 or dy != 0:
            self.canvas.move(self.text_id, dx, dy)
        self.coordinate[0] = x
        self.coordinate[1] = y

        for i in self.line_ids:
            try:
                orig_coords = self.canvas.coords(self.line_ids[i])
                if orig_coords != [self.coordinate[0], self.coordinate[1], i.coordinate[0], i.coordinate[1]]:
                    self.canvas.coords(self.line_ids[i], self.coordinate[0], self.coordinate[1], i.coordinate[0],
                                       i.coordinate[1])
            except KeyError:  # Line not yet created.
                pass

    def activate(self):
        try:
            self.canvas
        except AttributeError:
            return  # Not yet drawn.
        self.canvas.itemconfigure(self.text_id, fill=MarkovDraw.active_color)

    def activate_line_to(self, to):
        try:
            self.canvas.itemconfigure(self.line_ids[to], fill=MarkovDraw.active_line_color)
        except KeyError:
            print("KeyError on activate_line_to")
        except AttributeError:
            print("AttributeError on activate_line_to")

    def deactivate(self):
        try:
            self.canvas
        except AttributeError:
            return  # Not yet drawn.
        self.canvas.itemconfigure(self.text_id, fill=MarkovDraw.inactive_color)

    def remove_from_canvas(self):
        try:
            self.canvas
        except AttributeError:
            return  # Not yet drawn.
        for i in self.line_ids:
            self.canvas.delete(self.line_ids[i])
        self.canvas.delete(self.text_id)
        del self.canvas
        del self.text_id

    def move_to(self, x, y, duration, ease_in, ease_out):
        self.animated_x.animate(x, duration, ease_in, ease_out)
        self.animated_y.animate(y, duration, ease_in, ease_out)


# Nodes List.
nodes = list()
active_node = None
first_node = None
last_node=None

active_node_draw = None
nodes_draw = []

max_connections_per_node = 1


# Node initialization functions.
def order_list(lst, order):
    res = list()
    for i in range(len(lst)):
        res.append(tuple(lst[i - order + 1:i + 1]))

    return res


def split_by(s, mode):
    if mode == 'Word':
        return s.split(" ")
    elif mode == 'Character':
        return list(s)
    elif mode == 'Line':
        return s.split("\n")
    else:
        print("ERROR - Unexpected Mode2")
        exit()


def generate_chain(lst, mode):
    global nodes, active_node, first_node, last_node
    global canvas
    global input_options_progress
    global tk

    canvas.delete(ALL)
    nodes = list()
    active_node = None
    prev_node = None
    first_node = None
    last_node=None

    percentage = 0
    total = len(lst)
    for i in range(len(lst)):
        if i / total > percentage / 100:
            percentage += 1
            # print(percentage)
            input_options_progress.set(i / total * 100)
            tk.update()

        try:
            mn = nodes[bisect_left(nodes, lst[i])]  # Is this element already in the list of nodes?
        except IndexError:
            mn = None

        if mn == None or lst[i] != mn.value:  # It's not in the list, i guess.
            mn = MarkovNode(lst[i], mode)
            insort(nodes, mn)

        if first_node == None:
            first_node = mn

        if prev_node != None:
            prev_node.connect(mn)

        last_node=mn

        '''
        for j in nodes:  # TODO performance...
            if j.value == lst[i]:
                mn = j

        if mn == None:  # No Duplicates
            mn = MarkovNode(lst[i], mode)
            nodes.append(mn)

        if prev_node != None:
            prev_node.connect(mn)
        '''

        prev_node = mn

    global chain_info_numnodes
    chain_info_numnodes.set("Number of nodes: " + str(len(nodes)))
    chain_info_connections.set("Number of connections:" + str(len(lst)))
    chain_info_closed.set(["Chain is closed.", "Chain is open"][len(last_node.destination_nodes) == 0])
    print("Finished Generating Node Graph.")
    input_options_progress.set(0)

    print("Caching Unique nodes...")
    percentage = 0
    total = len(nodes)
    for i in range(len(nodes)):
        # print(i,nodes[i].value)
        if i / total > percentage / 100:
            percentage += 1
            # print(percentage)
            input_options_progress.set(i / total * 100)
            tk.update()

        nodes[i].cache_sorted_unique_destination()
    input_options_progress.set(0)


def parse_and_generate():
    global input_options_strip_newlines, input_options_strip_spaces, input_options_case
    print("Generating Chain...")

    mode = input_options_split_vars.get()
    order = int(input_options_order_vars.get())
    inp = input_input_box.get("1.0", 'end-1c')

    # print(input_options_strip_newlines.get(), input_options_strip_spaces.get())

    if input_options_strip_newlines.get() == "1":
        inp = inp.replace("\n", " ")
    if input_options_strip_spaces.get() == "1":
        inp = inp.replace(" ", "")
    if input_options_case.get() == "1":
        inp = inp.upper()
    split = split_by(inp, mode)
    # print("Split")

    ordered = order_list(split, order)
    # print("Ordered.")

    trimmed = [i for i in ordered if i]  # Remove blank elements.
    # print("Trimmed.")

    generate_chain(trimmed, mode)


generate = False


def start_generating_text():
    global generate
    generate = True
    follow_node()
    chain_options_generate.state(['disabled'])
    chain_options_stop.state(['!disabled'])


def stop_generating_text():
    global generate
    generate = False
    chain_options_generate.state(['!disabled'])
    chain_options_stop.state(['disabled'])


def follow_node():
    global generate, generate_delay
    global active_node, nodes, chain_results_box, to_be_active, nodes_draw, first_node
    global canvas

    if not generate:
        return

    # First step
    if active_node == None:
        to_be_active = first_node
    else:

        try:

            to_be_active = active_node.node.select()
            for i in nodes_draw:
                if i.node == to_be_active:
                    i.activate()
                    active_node.activate_line_to(i)
            active_node.deactivate()

        except EndOfChainError:
            stop_generating_text()
            return

    canvas.after(int(linear_map(0, 100, 0, 1500, generate_delay)), follow_node_part2)


def follow_node_part2():
    global generate, generate_delay
    global active_node, nodes, chain_results_box, to_be_active, nodes_draw, max_nodes
    global canvas
    global display_options_frame

    prev = [0, 0]
    for i in nodes_draw:
        if i.node == to_be_active:
            prev = i.coordinate

    if not active_node == None:
        # Remove previous
        active_node.remove_from_canvas()
        for i in nodes_draw:
            i.remove_from_canvas()
        nodes_draw = list()

    center = canvas_position_active()

    # print("Prev coords:", prev)
    active_node = MarkovDraw(to_be_active, canvas, prev[0], prev[1])

    active_node.activate()
    # print("Moving to:", center)
    active_node.move_to(center[0], center[1], (linear_map(0, 100, 0, 1.5, generate_delay)), True, True)

    destination_nodes = active_node.node.sorted_unique_destinations()[:max_nodes]

    if display_options_sort.get() == "0":
        shuffle(destination_nodes)

    others = canvas_position_connected(len(destination_nodes))
    others_outer = canvas_position_connected(len(destination_nodes), 3)
    # print(others)


    for i in range(len(destination_nodes)):
        if i >= max_nodes:
            break
        # print("Drawing destination:",i)
        # nodes_draw.append(MarkovDraw(destination_nodes[i],canvas, others_outer[i][0], others_outer[i][1]))
        # nodes_draw[-1].move_to(others[i][0], others[i][1], (linearMap(0, 100, 0, 1.5, generate_delay)), False, True)
        nodes_draw.append(MarkovDraw(destination_nodes[i], canvas, prev[0], prev[1]))
        nodes_draw[-1].move_to(others[i][0], others[i][1], (linear_map(0, 100, 0, 1.5, generate_delay)), True, True)
        nodes_draw[-1].deactivate()

    active_node.draw_lines(nodes_draw)

    chain_results_box.insert(END, active_node.node.get_last_value())

    if generate:
        tk.after(int(linear_map(0, 100, 0, 3000, generate_delay)), follow_node)


def update_canvas():
    global canvas
    global nodes_draw, active_node_draw

    t = time()
    for i in nodes_draw:
        i.update(t)
    if active_node != None:
        active_node.update(t)

    canvas.after(5, update_canvas)


# The position of the active node.
def canvas_position_active():
    global canvas
    w = canvas.winfo_width()
    h = canvas.winfo_height()
    # print(w,h)
    return (w / 2, h / 2)


# Positions of the connected nodes.
def canvas_position_connected(num, r_multiplier=1):
    w = canvas.winfo_width()
    h = canvas.winfo_height()
    r = min(h, w) / 3 * r_multiplier
    res = []
    for i in range(num):
        # ang=pi*(i+1)/(num+1)-pi/2
        ang = 2 * pi * i / num
        res.append((w / 2 + r * cos(ang), h / 2 + r * sin(ang)))
    return res


# Main UI Setup.
# Tk
tk = Tk()
tk.title("Markov Graphic Text Generator")

# Tk>Menu
menu = Notebook(tk, width=300, height=500)
menu.grid(column=1, row=1, sticky=(W, E, N, S))
tk.rowconfigure(1, weight=1)

# Tk>Menu>Input Tab
input_tab = Frame()
menu.add(input_tab, text="Input")

# Tk>Menu>Input Tab>Input
input_input_frame = LabelFrame(input_tab, text="Input")
input_input_frame.grid(column=1, row=1, sticky=(W, E, N, S))
input_tab.columnconfigure(1, weight=1)
input_tab.rowconfigure(1, weight=1)

# Tk>Menu>Input Tab>Input>Input Textbox
input_input_box = Text(input_input_frame, width=50)
input_input_box.grid(column=1, row=1, sticky=(W, E, N, S))
input_input_frame.columnconfigure(1, weight=1)
input_input_frame.rowconfigure(1, weight=1)

# Tk>Menu>Input Tab>Input>Input Clear Button
input_input_box_clear_btn = Button(input_input_frame, text="Clear",
                                   command=lambda: input_input_box.delete("1.0", 'end'))
input_input_box_clear_btn.grid(column=1, columnspan=2, row=2, sticky=(W, E, N, S))

# Tk>Menu>Input Tab>Input>Input Scrollbox
input_input_box_scroller = Scrollbar(input_input_frame, orient=VERTICAL, command=input_input_box.yview)
input_input_box_scroller.grid(column=2, row=1, sticky=(W, E, N, S))
input_input_box['yscrollcommand'] = input_input_box_scroller.set

# Tk>Menu>Input Tab>Options
input_options_frame = LabelFrame(input_tab, text="Options")
input_options_frame.grid(column=1, row=2, sticky=(W, E))
input_tab.columnconfigure(1, weight=1)

# Tk>Menu>Input Tab>Options>Strip Spaces
input_options_strip_spaces = Variable()
input_options_strip_spaces.set(0)
input_options_strip_spaces_btn = Checkbutton(input_options_frame, text='Strip Spaces ( _ )',
                                             variable=input_options_strip_spaces)
input_options_strip_spaces_btn.grid(column=1, row=2, columnspan=2, sticky=(W, E))

input_options_strip_newlines = Variable()
input_options_strip_newlines.set(0)
input_options_strip_newlines_btn = Checkbutton(input_options_frame, text='Newlines to Space ( \\n --> _ )',
                                               variable=input_options_strip_newlines)
input_options_strip_newlines_btn.grid(column=1, row=1, columnspan=2, sticky=(W, E))

input_options_case = Variable()
input_options_case.set(0)
input_options_case_btn = Checkbutton(input_options_frame, text='Ignore case',
                                     variable=input_options_case)
input_options_case_btn.grid(column=1, row=3, columnspan=2, sticky=(W, E))

# Tk>Menu>Input Tab>Options>Split-Label
input_options_split_label = Label(input_options_frame, text="Split By:")
input_options_split_label.grid(column=1, row=4, sticky=(W, E))
input_options_frame.columnconfigure(2, weight=1)

# Tk>Menu>Input Tab>Options>Split-RadioButton
input_options_split_vars = StringVar()


def input_options_split_vars_set():
    global input_options_split_vars
    global input_options_strip_spaces, input_options_strip_newlines
    if input_options_split_vars.get() == 'Character':
        pass
    elif input_options_split_vars.get() == 'Word':
        input_options_strip_spaces.set(0)
    elif input_options_split_vars.get() == 'Line':
        input_options_strip_spaces.set(0)
        input_options_strip_newlines.set(0)
    else:
        print("ERROR - Unexpected Mode3")
        exit()


input_options_split_char = Radiobutton(input_options_frame, text='Character', command=input_options_split_vars_set,
                                       variable=input_options_split_vars, value='Character')
input_options_split_char.grid(column=2, row=4, sticky=(W, E))
input_options_split_word = Radiobutton(input_options_frame, text='Word', command=input_options_split_vars_set,
                                       variable=input_options_split_vars, value='Word')
input_options_split_word.grid(column=2, row=5, sticky=(W, E))
input_options_split_line = Radiobutton(input_options_frame, text='Line', command=input_options_split_vars_set,
                                       variable=input_options_split_vars, value='Line')
input_options_split_line.grid(column=2, row=6, sticky=(W, E))
input_options_split_vars.set("Character")

# Tk>Menu>Input Tab>Options>Order-Label
input_options_order_label = Label(input_options_frame, text="Chain Order:")
input_options_order_label.grid(column=1, row=7, sticky=(W, E))

# Tk>Menu>Input Tab>Options>Order-Spinbox
input_options_order_vars = StringVar()
input_options_order = Spinbox(input_options_frame, textvariable=input_options_order_vars)
input_options_order['values'] = ('1', '2', '3', '4', '5')
input_options_order.grid(column=2, row=7, sticky=(W, E))

# Tk>Menu>Input Tab>Options>Generate
input_options_generate = Button(input_options_frame, text="Generate Graph", command=parse_and_generate)
input_options_generate.grid(column=1, row=8, columnspan=2, sticky=(W, E))

# Tk>Menu>Input Tab>Options>Progreess bar
input_options_progress = Variable()
input_options_progress_bar = Progressbar(input_options_frame, orient=HORIZONTAL, length=200,
                                         mode='determinate', variable=input_options_progress)
input_options_progress_bar.grid(column=1, row=9, columnspan=2, sticky=(W, E))

# Tk>Menu>Chain Tab
chain_tab = Frame()
menu.add(chain_tab, text="Chain")

# Tk>Menu>Chain Tab>Information
chain_info_frame = LabelFrame(chain_tab, text="Information")
chain_info_frame.grid(column=1, row=1, sticky=(W, E))
chain_tab.columnconfigure(1, weight=1)

# Tk>Menu>Chain Tab>Information>NumNodes
chain_info_numnodes = StringVar()
chain_info_numnodes_label = Label(chain_info_frame, textvariable=chain_info_numnodes)
chain_info_numnodes_label.grid(column=1, row=1, sticky=(W, E))

# Tk>Menu>Chain Tab>Information>NumNodes
chain_info_connections = StringVar()
chain_info_connections_label = Label(chain_info_frame, textvariable=chain_info_connections)
chain_info_connections_label.grid(column=1, row=2, sticky=(W, E))

# Tk>Menu>Chain Tab>Information>NumNodes
chain_info_closed = StringVar()
chain_info_closed_label = Label(chain_info_frame, textvariable=chain_info_closed)
chain_info_closed_label.grid(column=1, row=3, sticky=(W, E))

# Tk>Menu>Chain Tab>Options
chain_options_frame = LabelFrame(chain_tab, text="Options")
chain_options_frame.grid(column=1, row=2, sticky=(W, E))
chain_tab.columnconfigure(1, weight=1)

# Tk>Menu>Chain Tab>Options>Speed-Label
chain_options_speed_label = Label(chain_options_frame, text="Delay")
chain_options_speed_label.grid(column=1, row=1, sticky=(W, E))

# Tk>Menu>Chain Tab>Options>Speed-Slider
generate_delay = 1


def chain_options_speed_func(x):
    global generate_delay
    generate_delay = float(x)


chain_options_speed = Scale(chain_options_frame,
                            orient=HORIZONTAL, length=200, from_=1.0, to=100.0,
                            command=chain_options_speed_func)
chain_options_speed.set(30)
chain_options_speed.grid(column=2, row=1, sticky=(W, E))
chain_options_frame.columnconfigure(2, weight=1)

# Tk>Menu>Chain Tab>Options>Generate
chain_options_generate = Button(chain_options_frame, text="Generate Text", command=start_generating_text)
chain_options_generate.grid(column=1, row=3, columnspan=2, sticky=(W, E))

# Tk>Menu>Chain Tab>Options>Stop
chain_options_stop = Button(chain_options_frame, text="Stop", command=stop_generating_text)
chain_options_stop.grid(column=1, row=4, columnspan=2, sticky=(W, E))

# Tk>Menu>Chain Tab>Results
chain_results_frame = LabelFrame(chain_tab, text="Results")
chain_results_frame.grid(column=1, row=3, sticky=(W, E, N, S))
chain_tab.columnconfigure(1, weight=1)
chain_tab.rowconfigure(3, weight=1)

# Tk>Menu>Chain Tab>Results>Results Textbox
chain_results_box = Text(chain_results_frame, width=50)
chain_results_box.grid(column=1, row=1, sticky=(W, E, N, S))
chain_results_frame.columnconfigure(1, weight=1)
chain_results_frame.rowconfigure(1, weight=1)

# Tk>Menu>Chain Tab>Results>Results Scrollbox
chain_results_box_scroller = Scrollbar(chain_results_frame, orient=VERTICAL, command=chain_results_box.yview)
chain_results_box_scroller.grid(column=2, row=1, sticky=(W, E, N, S))
chain_results_box['yscrollcommand'] = chain_results_box_scroller.set

# Tk>Menu>Chain Tab>Results>Results Clear Btn
chain_results_box_clear_btn = Button(chain_results_frame, text="Clear",
                                     command=lambda: chain_results_box.delete("1.0", 'end'))
chain_results_box_clear_btn.grid(column=1, columnspan=2, row=2, sticky=(W, E, N, S))

# Tk>Menu>Display Tab
display_tab = Frame()
menu.add(display_tab, text="Display")

# Tk>Menu>Display Tab>Options
display_options_frame = LabelFrame(display_tab, text="Options")
display_options_frame.grid(column=1, row=1, sticky=(W, E))
display_tab.columnconfigure(1, weight=1)

# Tk>Menu>Display Tab>Options>Strip Spaces
display_options_sort = Variable()

display_options_sort_btn = Checkbutton(display_options_frame, text='Sort nodes',
                                       variable=display_options_sort)
display_options_sort_btn.grid(column=1, row=1, columnspan=3, sticky=(W, E))

display_options_sort.set("0")

# Tk>Menu>Display Tab>Options>Line Width-Label
display_options_line_width_label = Label(display_options_frame, text="Line Width")
display_options_line_width_label.grid(column=1, row=2, sticky=(W, E))

# Tk>Menu>Display Tab>Options>Line Width-Value
width_multiplier_str = StringVar()
display_options_max_nodes_label = Label(display_options_frame, textvariable=width_multiplier_str)
display_options_max_nodes_label.grid(column=2, row=2, sticky=(W, E))

# Tk>Menu>Display Tab>Options>Line Width-Slider
width_multiplier = 1


def set_line_width(x):
    global width_multiplier
    global width_multiplier_str
    width_multiplier = float(x)
    width_multiplier_str.set("{:.2f}".format(width_multiplier))


display_options_line_width = Scale(display_options_frame,
                                   orient=HORIZONTAL, length=200, from_=1.0, to=30.0,
                                   command=set_line_width)
display_options_line_width.set(15)
display_options_line_width.grid(column=3, row=2, sticky=(W, E))
display_options_frame.columnconfigure(3, weight=1)

# Tk>Menu>Display Tab>Options>Text Size-Label
display_options_text_size_label = Label(display_options_frame, text="Text Size")
display_options_text_size_label.grid(column=1, row=3, sticky=(W, E))

# Tk>Menu>Display Tab>Options>Text Size-Value
text_size_str = StringVar()
display_options_max_nodes_label = Label(display_options_frame, textvariable=text_size_str)
display_options_max_nodes_label.grid(column=2, row=3, sticky=(W, E))

# Tk>Menu>Display Tab>Options>Text Size-Slider
text_size = 1


def set_text_size(x):
    global text_size
    global text_size_str
    text_size = int(round(float(x)))
    text_size_str.set("{:.2f}".format(text_size))
    MarkovDraw.change_font_size(text_size)


display_options_text_size = Scale(display_options_frame,
                                  orient=HORIZONTAL, length=200, from_=1.0, to=100.0,
                                  command=set_text_size)
display_options_text_size.grid(column=3, row=3, sticky=(W, E))
display_options_text_size.set(24)

# Tk>Menu>Display Tab>Options>Max Nodes Displayed-Label
display_options_max_nodes_label = Label(display_options_frame, text="Max. nodes")
display_options_max_nodes_label.grid(column=1, row=4, sticky=(W, E))

# Tk>Menu>Display Tab>Options>Max Nodes Displayed-Value
max_nodes_str = StringVar()
display_options_max_nodes_label = Label(display_options_frame, textvariable=max_nodes_str)
display_options_max_nodes_label.grid(column=2, row=4, sticky=(W, E))

# Tk>Menu>Display Tab>Options>Max Nodes Displayed-Slider
max_nodes = 1


def set_max_nodes(x):
    global max_nodes
    global max_nodes_str
    max_nodes = int(round(float(x)))
    max_nodes_str.set(max_nodes)


display_options_max_nodes = Scale(display_options_frame,
                                  orient=HORIZONTAL, length=200, from_=1.0, to=300.0,
                                  command=set_max_nodes)
display_options_max_nodes.grid(column=3, row=4, sticky=(W, E))
display_options_max_nodes.set(100)

# Tk>Canvas
canvas = Canvas(tk, background="#FFFFFF", width=500, height=500)
canvas.grid(column=2, row=1, sticky=(W, E, N, S))
tk.columnconfigure(2, weight=1)

# Tk>Size grip
Sizegrip(tk).grid(column=999, row=999, sticky=(S, E))

update_canvas()

tk.mainloop()
