import mdl
import os
from display import *
from matrix import *
from draw import *

"""======== first_pass( commands ) ==========

  Checks the commands array for any animation commands
  (frames, basename, vary)

  Should set num_frames and basename if the frames
  or basename commands are present

  If vary is found, but frames is not, the entire
  program should exit.

  If frames is found, but basename is not, set name
  to some default value, and print out a message
  with the name being used.
  ==================== """
def first_pass( commands ):
    frames = False
    basename = False
    vary = False
    name = 'frame_name'
    num_frames = 1
    for command in commands:
        if command["op"] == "frames":
            frames = True
            num_frames = int(command["args"][0])
        elif command["op"] == "vary":
            vary = True
        elif command["op"] == "basename":
            basename = True
            name = command["args"][0]
    if vary and not frames:
        print("You need to specify a frame count to use vary.")
        exit()
    if frames and not basename:
        print("No basename set. Using 'frame_name' as basename.")
    return (name, num_frames)

"""======== second_pass( commands ) ==========

  In order to set the knobs for animation, we need to keep
  a separate value for each knob for each frame. We can do
  this by using an array of dictionaries. Each array index
  will correspond to a frame (eg. knobs[0] would be the first
  frame, knobs[2] would be the 3rd frame and so on).

  Each index should contain a dictionary of knob values, each
  key will be a knob name, and each value will be the knob's
  value for that frame.

  Go through the command array, and when you find vary, go
  from knobs[0] to knobs[frames-1] and add (or modify) the
  dictionary corresponding to the given knob with the
  appropriate value.
  ===================="""
def second_pass( commands, num_frames ):
    frames = [ {} for i in range(num_frames) ]
    for command in commands:
        if command["op"] == "vary":
            for frame in range(int(command["args"][0]), int(command["args"][1] + 1)):
                frames[frame][command["knob"]] = command["args"][2] + (command["args"][3] - command["args"][2]) * (frame - command["args"][0])/(command["args"][1] - command["args"][0])
    return frames


def run(filename):
    """
    This function runs an mdl script
    """
    p = mdl.parseFile(filename)

    if p:
        (commands, symbols) = p
    else:
        print "Parsing failed."
        return

    view = [0,
            0,
            1];
    ambient = [150,
               50,
               200]
    light = [[0.5,
              0.75,
              1],
             [255,
              255,
              255]]

    color = [0, 0, 0]
    symbols['.white'] = ['constants',
                         {'red': [0.2, 0.5, 0.5],
                          'green': [0.2, 0.5, 0.5],
                          'blue': [0.2, 0.5, 0.5]}]
    reflect = '.white'

    (name, num_frames) = first_pass(commands)
    frames = second_pass(commands, num_frames)
    for frame in range(num_frames):
        print str(frame) + str(frames[frame])
    ctr = 0
    step_3d = 100
    while ctr < num_frames:
        tmp = new_matrix()
        ident( tmp )

        stack = [ [x[:] for x in tmp] ]
        screen = new_screen()
        zbuffer = new_zbuffer()
        tmp = []
        consts = ''
        coords = []
        coords1 = []
        knob_value = 1
        for command in commands:
            c = command['op']
            args = command['args']
            if c == 'box':
                if command['constants']:
                    reflect = command['constants']
                add_box(tmp,
                        args[0], args[1], args[2],
                        args[3], args[4], args[5])
                matrix_mult( stack[-1], tmp )
                draw_polygons(tmp, screen, zbuffer, view, ambient, light, symbols, reflect)
                tmp = []
                reflect = '.white'
            elif c == 'sphere':
                if command['constants']:
                    reflect = command['constants']
                add_sphere(tmp,
                           args[0], args[1], args[2], args[3], step_3d)
                matrix_mult( stack[-1], tmp )
                draw_polygons(tmp, screen, zbuffer, view, ambient, light, symbols, reflect)
                tmp = []
                reflect = '.white'
            elif c == 'torus':
                if command['constants']:
                    reflect = command['constants']
                add_torus(tmp,
                          args[0], args[1], args[2], args[3], args[4], step_3d)
                matrix_mult( stack[-1], tmp )
                draw_polygons(tmp, screen, zbuffer, view, ambient, light, symbols, reflect)
                tmp = []
                reflect = '.white'
            elif c == 'line':
                add_edge(tmp,
                         args[0], args[1], args[2], args[3], args[4], args[5])
                matrix_mult( stack[-1], tmp )
                draw_lines(tmp, screen, zbuffer, color)
                tmp = []
            elif c == 'move':
                cpy = []
                if command["knob"] and command["knob"] in frames[ctr]:
                    for i in range(3):
                        cpy.append(args[i] - frames[ctr][command["knob"]] * args[i])
                    tmp = make_translate(cpy[0], cpy[1], cpy[2])
                else:
                    tmp = make_translate(args[0], args[1], args[2])
                matrix_mult(stack[-1], tmp)
                stack[-1] = [x[:] for x in tmp]
                tmp = []
            elif c == 'scale':
                cpy = []
                if command["knob"] and command["knob"] in frames[ctr]:
                    for i in range(3):
                        cpy.append(args[i] - frames[ctr][command["knob"]] * args[i])
                    tmp = make_scale(cpy[0], cpy[1], cpy[2])
                else:
                    tmp = make_scale(args[0], args[1], args[2])
                matrix_mult(stack[-1], tmp)
                stack[-1] = [x[:] for x in tmp]
                tmp = []
            elif c == 'rotate':
                theta = args[1] * (math.pi/180)
                if command["knob"] and command["knob"] in frames[ctr]:
                    theta *= frames[ctr][command["knob"]]
                if args[0] == 'x':
                    tmp = make_rotX(theta)
                elif args[0] == 'y':
                    tmp = make_rotY(theta)
                else:
                    tmp = make_rotZ(theta)
                matrix_mult( stack[-1], tmp )
                stack[-1] = [ x[:] for x in tmp]
                tmp = []
            elif c == 'push':
                stack.append([x[:] for x in stack[-1]] )
            elif c == 'pop':
                stack.pop()
            elif c == 'display':
                display(screen)
            elif c == 'save':
                save_extension(screen, args[0])
            # end operation loop
        ctr += 1
        if num_frames > 1:
            print(chr(27) + "[2J")
            print int(50 * ctr / num_frames) * "*" + (50 - int(50 * ctr / num_frames)) * "-"
            #display(screen)
            save_extension(screen, "anim/" + name + str(100 + ctr) + ".png")
    if num_frames > 1:
        print(chr(27) + "[2J")
        print("Making animation...")
        make_animation(name)

