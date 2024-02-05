import json
from structures import Position, Map
from cell import Cell

CELL_SIZE = 30
CELL_SPACE = 3
SPEED = 0.5
MOVE = CELL_SIZE + CELL_SPACE

def generate(map_: Map[Cell], record: str, output: str):

    with open(record) as file:
        json_data = json.load(file)
        data: list[list[tuple[int, int, int, int, bool]]] = json_data['data']
        init: list[tuple[int, int, int, int, bool]] = json_data['init']

    with open(output, 'w') as file:
        file.write(
'''<head>
    <style>
        rect.cell{
            width:''' + str(CELL_SIZE) + '''px;
            height:''' + str(CELL_SIZE) + '''px;
        }
        .cell{
            fill:rgb(160, 160, 160);
        }
        .wall{
            fill:red
        }
        .input{
            fill:rgb(77, 207, 77);
        }
        .output{
            fill:rgb(255, 255, 110);
        }
        .robot{
            width:''' + str(CELL_SIZE) + '''px;
            height:''' + str(CELL_SIZE) + '''px;
            fill:blue;
        }
        .robot .mail{
            fill: red;
            opacity: 1;
        }
        .robot[mail="false"] .mail{
            opacity: 0;
        }
    </style>
</head>
<body>
<svg width='''+str(map_.m*(MOVE))+'''px \
height='''+str(map_.n*(MOVE))+'''px>
<g>
''')
        for i in range(map_.n):
            for j in range(map_.m):
                file.write(f'<rect x={j*(MOVE)}px y={i*(MOVE)}px ')
                if not map_.has(Position(i, j)):
                    file.write("class='cell wall' ")
                elif map_[i, j].input_id is not None:
                    file.write("class='cell input' ")
                elif map_[i, j].output_id is not None:
                    file.write("class='cell output' ")
                else:
                    file.write("class='cell' ")
                file.write("/>\n")
        file.write("</g>")
        for i in range(len(init)):
            file.write(f'''<g class=robot id=r{i} \
transform="translate({init[i][2]*MOVE + CELL_SIZE/2}, \
{init[i][1]*MOVE + CELL_SIZE/2})\
rotate({-90*init[i][3]})" mail={'true' if init[i][4] else 'false'}>
    <rect width=20 height=20 x=-10 y=-10 />
    <rect class=mail width=10 height=10 x=-5 y=-5 />
    <rect width=3 height=8 x=-14 y=2 />
    <rect width=3 height=8 x=11 y=2 />
    </g>\n''')
        file.write("</g></svg>")
        file.write(f"<script>data={json.dumps(data)};CELL_SIZE={CELL_SIZE};CELL_SPACE={CELL_SPACE};MOVE={MOVE};SPEED={SPEED}</script>")
        file.write("<script>" + open("vis.js").read() + "</script>")
