Modelling of robotic mail sorting center
========================================
Problem statement
-----------------
### Given
- 2d Map of cell, for each cell:
    - its type, one of *empty*, *input*, *output*, *wall*; called *free* iff not *wall*
    - for *input* or *output* its unique *input id* or *output id* respectively
- Robot properties, (same for all robots for now):
    - *Time to move* for one cell
    - *Time to turn* for 90 degrees
    - *Time to take* a mail
    - *Time to put* a mail
- Initial robots' *state*: positions and directions and that they does not have mail.
- Probabilities or sequence of mails' destinations - for each *input id* a sequence or probabilities of *output id*s

### Find
For each robot its *action*s and start and end time of them such that no *conflict*s occur and mails are *processed correctly*.

At any time each robot is completing one *action* of:
- *idle* for any time, state is not changing.
- *move* for *time to move*, position is changing to neighbored cell in current robot direction.
- *turn* to direction for number of turn times *time to turn*, direction is changing to specified direction.
- *take* for *time to take*, robot is said to has mail to assigned destination.
- *put* for *time to put*, robot is said to does not have mail.

At any time for each pair of robots no *conflict*s occur:
- vertex conflict - two robots has the same position or one is moving to where other is.
- swap conflict - one is moving from A to B and other is moving from B to A.
- following conflict - one is moving to where other is moving from.

Each mail must be *processed correctly*:
- taken with *take* *action* when robot is on *input* cell, assign destination *output id* with the given probability or next in the given sequence.
- put with *put* *action* when robot is on *output* cell with the same *output id*.

Solution
--------
### General checker
Classes [`Robot`](robot.py#L19), [`Map`](structures.py#L66), [`Cell`](cell.py#L20), [`MailFactory`](mail_factories/mail_factory.py), [`Brain`](brains/brain.py#L14) represent modelling system which works as follows:
- Each *free* cell can be reserved by one robot and unreserved by the same robot; methods `Cell.reserve` and `Cell.unreserve`
- *Input* cells calls `MailFactory` with its *input id* to get mails later.
- if cell is *input*, when robot calls `Cell.get_input` to get new mail, cell calls saved `MailFactory` call.
- At start time, each robot reserves cell which it is on.
- After completing *action*, robot calls `Brain.get_next_action`:
    - if *action* is *idle*, robot waits for brain to call `Robot.abort`
    - if *action* is *move*, robot reserves next cell, waits for *time to move*, unreserves previous cell; if next cell is *wall* or not exist or already reserved, `NotFreeCellException` or `PositionOutOfMapException` or `CellIsReservedException` raises correspondingly;
    - if *action* is *turn*, robot waits for *time to turn*
    - if *action* is *take*, robot tries to take mail from cell and waits for *time to take*; if robot has mail `RobotWithMailException` raises; if cell is not *input* `NotInputCellException` raises.
    - if *action* is *put*, robot tries to put mail from cell and waits for *time to put*; if robot does not have mail `RobotWithoutMailException` raises; if mail *output id* is not cell *output id* or cell is not *output*, `IncorrectOutputException` raises.

### Online decisions
In a group of possible solutions it is cheap to compute online for every robot position and direction next action, robot can wait for next cell to free for some time. Thus, [`SafeRobot`](robot.py#L155), [`SafeCell`](cell.py#L90), [`OnlineBrain`](brains/brain.py#L34) helps to implement these solutions as follows:
- Each *free* cell can be reserved and return event which occurs when cell is unreserved.
- So, if robot receives *move* *action* it does *idle* action until next cell is unreserved.
- Brain calls protected methods and sends *obvious* *action*s automatically:
    - `OnlineBrain._mail_taken` and *take* if robot is on assigned *input* cell and does not have mail.
    - `OnlineBrain._mail_put` and *put* if robot is on required by mail *output* cell.
- Brain calls protected methods `OnlineBrain._go_with_mail` and `OnlineBrain._go_without_mail` when *action* is not *obvious*. If they return only *move* and *turn* *action*s only `PositionOutOfMapException` can be raised.

### Precompute direction
It is possible to orientate each edge between neighbors cell so that no cycle with length less than number of robot exists, and the map is strongly connected (or except some *empty* cells).
For each cell and each *input* and *output* cell define direction so that if robot goes to that direction, it will be eventually in corresponding *input* and *output* cell.
Give *take* and *pup* actions if no conflicts occur, give *turn* action if defined direction is other than current, give *move* action as soon as no conflicts will occur.

Algorithm is implemented as [`DirectionBrain`](brains/direction_brain.py).

### Sequentially find path
A Map has special *rest* cells as many as robots so that the map without all of *rest* cells is connected and each *rest* cell is connected to non *rest*.
Assign each robot to one *rest* cell and assume that at the start, they stay on the corresponding cell.
For each cell, non intersecting intervals (start and end time) are stored, that corresponds to time when robots will occupy that cell. For each robot future path is stored. At the start for each *rest* cell add intervals from zero to infinity.
At the start time sequentially for each robot find nonintersecting path in space\*time space (using Dijkstra or A* algorithms) from current position to *input* cell and then to its *rest* cell, store found path and for each cell in path add interval (from time when robot will start moving to that cell to time when robot will end moving from that cell, for the *rest* cell add interval until infinity).
When robot takes or puts mail, clear its path and delete all corresponding intervals, find and add in the same way new path from current position to *input* or *output* cell and then to robot's *rest* cell.
The Algorithms guarantees that required path always exists since path to its rest place exists as it was not previously intersected, on its *rest* cell robot can stay any time until all other robots will reach their *rest* cells, then robot can find path to destination as the map without *rest* cells (the only with intervals) is connected.

Algorithm is implemented as [`PathBrain`](brains/path_brain.py).Al

### Ant colony optimization algorithm
[`AntBrain`](brains/ant_brain.py), description...
