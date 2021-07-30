import svgwrite
import pyqrcode
import uuid
import base64
import shortuuid
import math
import argparse

# parser = argparse.ArgumentParser(prog='qr-generator', description='Process some integers.')

# # Add the arguments
# parser.add_argument('Path', type=str, help='the path to list')

# # Execute the parse_args() method
# args = parser.parse_args()

# input_path = args.Path

# dwg = svgwrite.Drawing('test.svg', profile='tiny')
# dwg.add(dwg.line((0, 0), (10, 0), stroke=svgwrite.rgb(10, 10, 16, '%')))
# dwg.add(dwg.text('Test', insert=(0, 0.2), fill='red'))
# dwg.save()

page_size = (612, 792)
# spacing = (139.5463, 90)
label_size = (99, 40.4375)
qr_width = label_size[0]
if label_size[0] > label_size[1] :
    qr_width = label_size[1]

# grid_size = (3, 10)
# rotation_offset = (0, 0)
# label_offset = (0, 0)
# tag_rotation = 0

# initial_offset = ((page_size[0] - (((grid_size[0] - 1) * spacing[0]) + label_size[0]))/2,
#     (page_size[1] - (((grid_size[1] - 1) * spacing[1]) + label_size[1]))/2)
# initial_offset = (20.41, 22.5358)
# print('initial_offset', initial_offset)
dwg = svgwrite.Drawing('test3.svg', size = page_size)
# dwg.embed_font('Urbane', '/Users/colinwillson/Library/Fonts/Urbane 9.otf')


# dwg.translate(initial_offset)
label_size = (99, 40.5) # size of label in pixels (X, Y)
def get_translation( index ):
    orientation_portrait = True # Portrait or lanscape orientation
    label_padding = (5, 5) # Space from outter edge of label to print text/content
    start_offset = (22.9968, 72.438) # Coordinate of upper left label's upper left corner in pixels (X, Y)
    
    grid_size = (5, 16) # Label count (X, Y)
    margin = (18, 0) # Space between labels (X, Y)
    rotation = 0 # Rotation of initial label

    trans_x = start_offset[0] + (math.floor(index / grid_size[1]) * (label_size[0] + margin[0]))
    trans_y = start_offset[1] + ((index % grid_size[1]) * (label_size[1] + margin[1]))
    label_translation = (trans_x, trans_y, 0) # (X, Y, Rotation)

    if index < grid_size[0] * grid_size[1]:
        return label_translation
    else :
        return None


i = 0
while True :
# for i in range(grid_size[0] * grid_size[1]):
    label_trans = get_translation(i)

    if label_trans == None :
        break
    # print(qr.text())
    # tag_offset = (spacing[0] * i, spacing[1] * i)
    # tag_rotation = 0
    # qr_text = str(uuid.uuid1()) #base64.urlsafe_b64encode(uuid.uuid1().bytes).rstrip(b'=').decode('ascii')
    qr_text = shortuuid.uuid()[:12]
    # qr_text = '12345'
    print('uuid', qr_text)
    qr = pyqrcode.create(qr_text)
    qrData = qr.text()
    print('qr_text', qr_text)
    # blocks_per_line = len(qrData) ** 2
    blocks_per_line = 0
    while qrData[blocks_per_line] != '\n':
        blocks_per_line += 1

    block_size = qr_width/blocks_per_line
    # print(block_size)
    x = 0
    y = 0

    new_group = dwg.defs.add(dwg.g(id = qr_text))

    # Constructo QR Code block by block
    for square in qrData:
        if square == '\n':
            y += 1
            x = 0
        else: 
            currennt_cord = (x * block_size, y * block_size)
            
            new_group.add(dwg.rect(currennt_cord, (block_size, block_size), fill='white' if int(square) == 0 else 'black'))
            x += 1

    # Add text next to the code
    title_text_size = 7
    id_text_size = 6
    text_offset = 0
    new_group.add(dwg.text('Waffle Track',
        insert=(qr_width, 10),
        fill='#1a2c6e',
        font_size='{}px'.format(title_text_size),
        font_weight="bold",
        # text_anchor='middle',
        # alignment_baseline='central',
        font_family="Helvetica"))
    new_group.add(dwg.text('Inventory Tag',
        insert=(qr_width, title_text_size + 11),
        fill='black',
        font_size='{}px'.format(title_text_size),
        # font_weight="bold",
        # text_anchor='middle',
        # alignment_baseline='central',
        font_family="Helvetica"))
    new_group.add(dwg.text(qr_text,
        insert=(qr_width, title_text_size + id_text_size + 14),
        fill='black',
        font_size='{}px'.format(id_text_size),
        # font_weight="bold",
        # text_anchor='middle',
        # alignment_baseline='central',
        font_family="Helvetica"))

    # column_ref = i % 2
    # row_ref =  trunc(i / 1)
    # if i % 2 != 0:
    #     column_ref = 1
    # new_group.translate(initial_offset)
    # new_group.translate(5, label_size[1]/2)
    # new_group.translate((spacing[0] * ((i % grid_size[0]))), (spacing[1] * math.trunc(i / grid_size[0])))
    # new_group.translate(-qr_width/2, 0)
    # new_group.rotate(tag_rotation, rotation_offset)
    # new_group_inverted = dwg.add(new_group)
    # new_group.rotate(180)
    # dwg.add(new_group)
    ng = dwg.use(new_group)
    # ngi = dwg.use(new_group)
    # ngi.translate(label_size[0], 0)
    # ngi.rotate(180)

    label_group = dwg.g(id = '{}-group'.format(qr_text))
    label_group.add(ng)
    # pair_group.add(ngi)
    
    
    label_group.translate(label_trans[0], label_trans[1])
    
    # x = (((i % 2) * 133.23) + (math.trunc(i / 10) * 256.5356))
    # y = (i % 10) * 39.6851
    # pair_group.translate((((i % 2) * 133.23)),
    #     (i % 2) * 39.6851)
    
    # pair_group.translate((((i % 2) * 133.23) + (math.trunc(i / 10) * 256.5351)),
    #     ((i % 10)/2 * 113.3851) - ((i % 2) * 17.0075))
    dwg.add(label_group)

    i += 1
# dwg = svgwrite.Drawing('test.svg', profile='tiny')
# dwg.add(dwg.line((0, 0), (10, 0), stroke=svgwrite.rgb(10, 10, 16, '%')))
dwg.save()
