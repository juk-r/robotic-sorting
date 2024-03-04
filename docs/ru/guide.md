# Как устроены [примеры](/examples)
1. Импортировать классы:
```python
from modelling import Model
from import_data impoty import_json, import_map, import_distribution
from structures import Direction, Position
from robot import Robot, RobotType
```
2. Импортировать нужный алгоритм:
```python
from brains import chosen_brain # <нужный класс>
```
4. Создать модель
```python
model = Model()
```
5. Создать генератор направлений
```python
factory = import_distribution(model, import_json('path/to/distribution.json'))
```
6. Задать карту через json
```python
model.set_map(import_map(model, import_json('path/to/map.json', factory))[0])
```
или csv
```python
model.set_map(import_map_csv(model, 'path/to/map.csv', 'path/to/map/details.csv', mail_factory))
```
7. Задать алгоритм:
```python
model.set_brain(chosen_brain(...))
```
8. Задать времена, за которые робот выполняет действия
```python
robot_type = RobotType(
    time_to_move=...,
    time_to_turn=...,
    time_to_put=...,
    time_to_take=...,
)
```
9. Добавить нужное количество роботов
```python
x: int
y: int
direction: Direction.up | Direction.left | Direction.down | Direction.right
model.add_robot(Robot(model, robot_type, Position(x, y), direction))
```
10. Запустить одно из
- `model.run(time)` просто запустить
- `model.record_actions(mail_count, file_path))` записать все действия роботов
- `model.test(time, count)` чтобы получить среднее количество доставленных грузов и отклонение
