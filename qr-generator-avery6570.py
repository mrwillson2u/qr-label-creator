import svgwrite
import pyqrcode
import uuid
import base64
import shortuuid
import math

# dwg = svgwrite.Drawing('test.svg', profile='tiny')
# dwg.add(dwg.line((0, 0), (10, 0), stroke=svgwrite.rgb(10, 10, 16, '%')))
# dwg.add(dwg.text('Test', insert=(0, 0.2), fill='red'))
# dwg.save()

page_size = (612, 792)
spacing = (139.5463, 90)
label_size = (126, 90)
qr_width = label_size[1] - 10
grid_size = (4, 8)
label_offset = (qr_width/2, 0)
# label_offset = (0, 0)
tag_rotation = 270

initial_offset = ((page_size[0] - (((grid_size[0] - 1) * spacing[0]) + label_size[0]))/2,
    (page_size[1] - (((grid_size[1] - 1) * spacing[1]) + label_size[1]))/2)
# initial_offset = (0, 0)
print('initial_offset', initial_offset)
dwg = svgwrite.Drawing('test3.svg', size = page_size)
# dwg.embed_font('Urbane', '/Users/colinwillson/Library/Fonts/Urbane 9.otf')

# dwg.translate(initial_offset)

for i in range(grid_size[0] * grid_size[1]):

    # print(qr.text())

    

    tag_offset = (spacing[0] * i, spacing[1] * i)
    # tag_rotation = 0
    # qr_text = str(uuid.uuid1()) #base64.urlsafe_b64encode(uuid.uuid1().bytes).rstrip(b'=').decode('ascii')
    qr_text = shortuuid.uuid()[:12]
    # qr_text = '12345'
    print('uuid', qr_text)
    qr = pyqrcode.create(qr_text)
    qrData = qr.text()
    # blocks_per_line = len(qrData) ** 2
    blocks_per_line = 0
    while qrData[blocks_per_line] != '\n':
        blocks_per_line += 1

    block_size = qr_width/blocks_per_line
    # print(block_size)
    x = 0
    y = 0

    new_group = dwg.g(id = 'test')
    # new_group.translate(initial_offset)

    for square in qrData:
        if square == '\n':
            y += 1
            x = 0
        else: 
            currennt_cord = (x * block_size, y * block_size)
            
            new_group.add(dwg.rect(currennt_cord, (block_size, block_size), fill='white' if int(square) == 0 else 'black'))
            x += 1

    title_text_height = 12
    id_text_size = 8
    text_offset = 0

    new_group.add(dwg.text('nSight',
        insert=(qr_width/2, qr_width + title_text_height),
        fill='#cc0000',
        font_size='{}px'.format(title_text_height),
        font_weight="bold",
        text_anchor='middle',
        # alignment_baseline='central',
        font_family="Helvetica"))
    new_group.add(dwg.text('Inventory',
        insert=(qr_width/2, qr_width + 2 + (title_text_height * 2)),
        fill='black',
        font_size='{}px'.format(title_text_height),
        # font_weight="bold",
        text_anchor='middle',
        # alignment_baseline='central',
        font_family="Helvetica"))
    new_group.add(dwg.text(qr_text,
        insert=(qr_width/2, qr_width + title_text_height + 25),
        fill='black',
        font_size='{}px'.format(id_text_size),
        # font_weight="bold",
        text_anchor='middle',
        # alignment_baseline='central',
        font_family="Helvetica"))

    # column_ref = i % 2
    # row_ref =  trunc(i / 1)
    # if i % 2 != 0:
    #     column_ref = 1
    new_group.translate(initial_offset)
    new_group.translate(5, label_size[1]/2)
    new_group.translate((spacing[0] * ((i % grid_size[0]))), (spacing[1] * math.trunc(i / grid_size[0])))
    new_group.translate(-qr_width/2, 0)
    new_group.rotate(tag_rotation, label_offset)
    dwg.add(new_group)
# dwg = svgwrite.Drawing('test.svg', profile='tiny')
# dwg.add(dwg.line((0, 0), (10, 0), stroke=svgwrite.rgb(10, 10, 16, '%')))
dwg.save()
