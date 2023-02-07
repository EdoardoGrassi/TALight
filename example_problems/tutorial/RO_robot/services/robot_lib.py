#!/usr/bin/env python3

import logging
from dataclasses import dataclass
from typing import Dict, Final, List, Tuple, TypeVar

from RO_verify_submission_gen_prob_lib import verify_submission_gen

_UNWALKABLE = -1
"""Magic value of a cell that cannot be traversed."""

_LOGGER = logging.getLogger(__package__).getChild("robot")

instance_objects_spec = [
    ("grid", "matrix_of_int"),
    ("budget", int),
    ("diag", bool),
    ("cell_from", "list_of_str"),
    ("cell_to", "list_of_str"),
    ("cell_through", "list_of_str"),
]
additional_infos_spec = [
    ("partialDP_to", "matrix_of_int"),
    ("partialDP_from", "matrix_of_int"),
]
answer_objects_spec = {
    "num_paths": "int",                       # the number of feasible paths
    # the number of feasible paths that collect the maximum total prize
    "num_opt_paths": "int",
    # the maximum total prize a feasible path can collect
    "opt_val": "int",
    # a path collecting the maximum possible total prize
    "opt_path": "list_of_cell",
    "list_opt_paths": "list_of_list_of_cell",  # the list of all optimum paths
    # the DP table meant to tell the number of paths from top-left cell to the generic cell
    "DPtable_num_to": "matrix_of_int",
    # the DP table meant to tell the number of paths from the generic cell to the bottom-right cell"
    "DPtable_num_from": "matrix_of_int",
    # the DP table meant to tell the maximum value of a feasible path path moving from top-left cell to the generic cell
    "DPtable_opt_to": "matrix_of_int",
    # the DP table meant to tell the maximum value of a feasible path moving from the generic cell to the bottom-right cell
    "DPtable_opt_from": "matrix_of_int",
    # the DP table meant to tell the number of optimal paths from top-left cell to the generic cell"
    "DPtable_num_opt_to": "matrix_of_int",
    # the DP table meant to tell the number of optimal paths from the generic cell to the bottom-right cell.
    "DPtable_num_opt_from": "matrix_of_int",
}

answer_objects_implemented = [
    'num_paths',
    'num_opt_paths',
    'opt_val',
    'opt_path',
    'list_opt_paths',
    'DPtable_num_to',
    'DPtable_num_from',
    'DPtable_opt_to',
    'DPtable_opt_from',
    'DPtable_num_opt_to',
    'DPtable_num_opt_from'
]

limits = {
    'CAP_FOR_NUM_SOLS': 100,
    'CAP_FOR_NUM_OPT_SOLS': 100
}

_T = TypeVar("_T")

_Cell = Tuple[int, int]
_Mat = List[List[_T]]


def _xmap(x: int) -> int:
    """Map internal x coordinate of a cell to a human-readable format."""
    return x + 1


def _ymap(y: int) -> str:
    """Map internal y coordinate of a cell to a human-readable format."""
    return chr(ord('A') + y)


def _map(x, y):
    return f"({_xmap(x)},{_ymap(y)})"


def parse_cell(cell: str) -> _Cell:
    # Take row and col
    #cell = cell[1:-1]
    #row, col = cell.split(",")
    #row, col = ord(row.lower()) - ord("a"), int(col)
    row, col = cell
    row, col = int(row) - 1, ord(col.lower()) - ord("a")
    return (row, col)


def walkable(grid: _Mat[int], cell: _Cell) -> bool:
    """Checks whether a cell is free or forbidden."""
    assert grid is not None
    assert cell is not None
    x, y = cell
    return grid[x][y] != _UNWALKABLE


def check_matrix_shape(f: _Mat) -> bool:
    """Checks if matrix is empty."""
    if not f:
        return False

    """Checks if list is a matrix."""
    cols = len(f[0])
    if cols == 0:
        return False

    for row in f:
        if len(row) != cols:
            return False

    return True

def check_budget_bounds(budget: int) -> bool:
    """Check if the allocated budget is within the bounds specified by the problem."""
    # TODO: finalize the value of the upper bound
    return 0 < budget <= 100

def check_contains_cell(grid: _Mat, cell: _Cell) -> bool:
    """Check if the coordinates map to a valid cell."""
    assert grid is not None
    assert cell is not None
    rows, cols = shape(grid)
    return 0 <= cell[0] < rows and 0 <= cell[1] < cols


def shape(grid: _Mat) -> Tuple[int, int]:
    """
    Return:
        (number of rows, number of columns) of matrix
    """
    return len(grid), len(grid[0])


def check_instance_consistency(instance):
    _LOGGER.debug("instance = %s", instance)
    grid = instance['grid']
    rows, cols = shape(grid)
    # TODO: ask whether this check is necessary for the type 'matrix_of_int'
    if not check_matrix_shape(grid):
        print(f"Error: {grid} must be a matrix")
        exit(0)

    for row in range(len(grid)):
        for col in range(len(grid[row])):
            if (c := grid[row][col]) < -1:
                print(f"Error: value {c} in {_map(row, col)} is not allowed")
                exit(0)

    if grid[0][0] == -1 or grid[-1][-1] == -1:
        print(f"Error")
        exit(0)

    # TODO: validate cells coordinates
    for argname in ["cell_from", "cell_to", "cell_through"]:
        cell = parse_cell(instance[argname])
        if cell[0] > rows or cell[1] > cols:
            print(f"Invalid {argname} {cell}")
            exit(0)



def cost(grid: _Mat, cell: _Cell) -> int:
    """Cost on the budget to traverse a cell."""
    x, y = cell
    # only cells with negative values have a cost
    return max(-grid[x][y], 0)


def build_cost_table(grid: _Mat) -> _Mat:
    """Build the cost table associated with a grid."""
    assert grid is not None
    assert check_matrix_shape(grid)

    rows, cols = shape(grid)
    costs = [[cost(grid, (row, col)) for col in range(cols)] for row in range(rows)]
    assert shape(costs) == shape(grid)
    return costs


def dptable_num_to_with_budget(grid: _Mat[int], budget: int, diag: bool = False) -> _Mat:
    assert check_matrix_shape(grid)
    assert check_budget_bounds(budget)

    rows, cols = shape(grid)
    dptable = [[[0 for _ in range(cols)] for _ in range(rows)] for _ in range(budget)]
    
    for b in range(budget):
        assert shape(dptable[b]) == shape(grid)
    
    costs = build_cost_table(grid)
    dptable[0][0][0] = 1
    # iterate on each cell of the grid, except the last row and column
    for row in range(rows - 1):
        for col in range(cols - 1):

            # iterate on all budget values that we may have when reaching the cell
            for b in range(budget):
                # try moving vertically by checking the cost of the move
                c = costs[row + 1][col] + b
                assert c >= 0
                if c < budget:
                    dptable[c][row + 1][col] += dptable[b][row][col]

                # try moving horizontally by checking the cost of the move
                c = costs[row][col + 1] + b
                assert c >= 0
                if c < budget:
                    dptable[c][row][col + 1] += dptable[b][row][col]

                if diag:
                    # try moving diagonally by checking the cost of the move
                    c = costs[row + 1][col + 1] + b
                    assert c >= 0
                    if c < budget:
                        dptable[c][row + 1][col + 1] += dptable[b][row][col]

    # iterate on the last column, we can only move vertically
    for row in range(rows - 1):
        for b in range(budget):
            c = costs[row][-1] + b
            if c < budget:
                dptable[c][row + 1][-1] += dptable[b][row][-1]

    # iterate on the last row, we can only move horizontally
    for col in range(cols - 1):
        for b in range(budget):
            c = costs[-1][col] + b
            assert c >= 0
            if c < budget:
                dptable[c][-1][col + 1] += dptable[b][-1][col]

    return dptable


def dptable_num_to(grid: _Mat[int], diag: bool = False) -> _Mat:
    """
    Build an acceleration table suitable for counting the number of paths.
    Construction starts from the cell in the top-left corner.

    Args:
        f:    game field table
        diag: allow diagonal moves

    Returns:
        A table where each cell contains the maximum utility value of any path starting from it.
    """
    assert check_matrix_shape(grid)

    rows, cols = shape(grid)

    b = [[0 for _ in range(cols)] for _ in range(rows)]  # budget left at cell
    for i in range(1, cols):
        b[0][i] = b[0][i - 1] + min(grid[0][i])

    for i in range(1, rows):
        b[i][0] = b[i - 1][0] + min(grid[i][0])

    for i in range(1, rows):
        for j in range(1, cols):
            b[i]

    t = [[0 for _ in range(cols)]
         for _ in range(rows)]  # number of paths at cell
    # NOTE: cells default to zero, in some cases there is no need to assing values
    t[0][0] = 1
    for i in range(1, cols):
        newbudget = b[0][i - 1] - min(grid[0][i], 0)
        if newbudget < budget:
            t[0][i] = t[0][i - 1]
            b[0][i] = newbudget

    for i in range(1, rows):
        newbudget = b[i - 1][0] - min(grid[i][0], 0)
        if walkable(grid, (i, 0)):
            t[i][0] = t[i - 1][0]

    for i in range(1, rows):
        for j in range(1, cols):
            if walkable(grid, (i, j)):
                if diag:
                    t[i][j] = t[i][j - 1] + t[i - 1][j] + t[i - 1][j - 1]
                else:
                    t[i][j] = t[i][j - 1] + t[i - 1][j]

    assert shape(grid) == shape(t)
    return t


def dptable_num_from(g: _Mat[int], diag: bool = False) -> _Mat:
    """
    Build an accelerator table suitable for counting the number of paths.
    Construction starts from the cell in the bottom-right corner.

    Args:
        f:    game field table
        diag: allow diagonal moves
    """
    assert check_matrix_shape(g)

    rows, cols = shape(g)
    t = [[0 for _ in range(cols)] for _ in range(rows)]

    # NOTE: cells default to zero, in some cases there is no need to assing values
    t[-1][-1] = 1
    for i in reversed(range(cols - 1)):
        if walkable(g, (-1, i)):
            t[-1][i] = t[-1][i + 1]

    for i in reversed(range(rows - 1)):
        if walkable(g, (i, -1)):
            t[i][-1] = t[i + 1][-1]

    if diag:
        for i in reversed(range(rows - 1)):
            for j in reversed(range(cols - 1)):
                if walkable(g, (i, j)):
                    t[i][j] = t[i][j + 1] + t[i + 1][j] + t[i + 1][j + 1]

    else:
        for i in reversed(range(rows - 1)):
            for j in reversed(range(cols - 1)):
                if walkable(g, (i, j)):
                    t[i][j] = t[i][j + 1] + t[i + 1][j]

    assert shape(g) == shape(t)
    return t


def dptable_opt_to(g: _Mat, diag: bool = False) -> _Mat:
    """
    Build an accelerator table suitable for finding the maximum value.
    Construction starts from the cell in the bottom-right corner.

    Args:
        f:    game field table
        diag: allow diagonal moves

    Returns:
        A table where each cell contains the maximum utility value
        of any path that starts from that cell.
    """
    assert g is not None
    assert check_matrix_shape(g)

    rows, cols = shape(g)
    t = [[0 for _ in range(cols)] for _ in range(rows)]

    t[0][0] = g[0][0]
    for i in range(1, cols):
        if walkable(g, (0, i)):
            t[0][i] = g[0][i] + t[0][i - 1]

    for i in range(1, rows):
        if walkable(g, (i, 0)):
            t[i][0] = g[i][0] + t[i - 1][0]

    if diag:
        for i in range(1, rows):
            for j in range(1, cols):
                if walkable(g, (i, j)):
                    t[i][j] = g[i][j] + \
                        max([t[i][j - 1], t[i - 1][j], t[i - 1][j - 1]])

    else:
        for i in range(1, rows):
            for j in range(1, cols):
                if walkable(g, (i, j)):
                    t[i][j] = g[i][j] + max(t[i][j - 1], t[i - 1][j])

    return t


def dptable_opt_from(g: _Mat, diag: bool = False) -> _Mat:
    """
    Build an accelerator table suitable for finding the maximum value.
    Construction starts from the cell in the bottom-right corner.

    Args:
        f:    game field table
        diag: allow diagonal moves

    Returns:
        A table where each cell contains the maximum utility value
        of any path that ends at that cell.
    """
    assert check_matrix_shape(g)

    rows, cols = shape(g)
    t = [[0 for _ in range(cols)] for _ in range(rows)]

    t[-1][-1] = g[-1][-1]
    for i in reversed(range(cols - 1)):
        if walkable(g, (-1, i)):
            t[-1][i] = g[-1][i] + t[-1][i + 1]

    for i in reversed(range(rows - 1)):
        if walkable(g, (i, -1)):
            t[i][-1] = g[i][-1] + t[i + 1][-1]

    if diag:
        for i in reversed(range(rows - 1)):
            for j in reversed(range(cols - 1)):
                if walkable(g, (i, j)):
                    t[i][j] = g[i][j] + \
                        max([t[i][j + 1], t[i + 1][j], t[i + 1][j + 1]])

    else:
        for i in reversed(range(rows - 1)):
            for j in reversed(range(cols - 1)):
                if walkable(g, (i, j)):
                    t[i][j] = g[i][j] + max(t[i][j + 1], t[i + 1][j])

    return t


@dataclass
class NumOptCell:
    count: int  # the count of optimal paths ending at this cell
    value: int  # the optimal value of a path ending at this cell


def dptable_num_opt_to(g: _Mat, diag: bool = False) -> _Mat:
    """
    Build a DP table suitable for finding the maximum value.
    Construction starts from the cell in the bottom-right corner.

    Args:
        g:    game field table
        diag: allow diagonal moves
    """
    assert check_matrix_shape(g)

    rows, cols = shape(g)
    # NOTE: store (num_of_paths, opt_value) for each cell
    t = [[NumOptCell(count=0, value=0) for _ in range(cols)]
         for _ in range(rows)]

    t[0][0].count = 1
    t[0][0].value = g[0][0]
    for i in range(1, cols):  # fill first row
        if walkable(g, (0, i)):
            t[0][i].count = t[0][i - 1].count
            t[0][i].value = g[0][i] + t[0][i - 1].value

    for i in range(1, rows):  # fill first column
        if walkable(g, (i, 0)):
            t[i][0].count = t[i - 1][0].count
            t[i][0].value = g[i][0] + t[i - 1][0].value

    if diag:
        for i in range(1, rows):
            for j in range(1, cols):
                if walkable(g, (i, j)):
                    neighbors = [t[i][j - 1], t[i - 1][j], t[i - 1][j - 1]]
                    maxvalue = max(neighbors, key=lambda x: x.value).value
                    t[i][j].count = sum(map(lambda x: x.count,
                                            filter(lambda x: x.value == maxvalue, neighbors)))
                    t[i][j].value = g[i][j] + maxvalue

    else:
        for i in range(1, rows):
            for j in range(1, cols):
                if walkable(g, (i, j)):
                    neighbors = [t[i][j - 1], t[i - 1][j]]
                    maxvalue = max(neighbors, key=lambda x: x.value).value
                    t[i][j].count = sum(map(lambda x: x.count,
                                            filter(lambda x: x.value == maxvalue, neighbors)))
                    t[i][j].value = g[i][j] + maxvalue

    return as_tuple_matrix(t)


def dptable_num_opt_from(g: _Mat, diag: bool = False) -> _Mat:
    """
    Build a DP table suitable for finding the maximum value.
    Construction starts from the cell in the bottom-right corner.

    Args:
        g:    game field table
        diag: allow diagonal moves
    """
    assert check_matrix_shape(g)

    rows, cols = shape(g)
    # NOTE: store (num_of_paths, opt_value) for each cell
    t = [[NumOptCell(count=0, value=0) for _ in range(cols)]
         for _ in range(rows)]

    t[-1][-1].count = 1
    t[-1][-1].value = g[-1][-1]
    for i in reversed(range(cols - 1)):  # fill last row
        if walkable(g, (-1, i)):
            t[-1][i].count = t[-1][i + 1].count
            t[-1][i].value = g[-1][i] + t[-1][i + 1].value

    for i in reversed(range(rows - 1)):  # fill last column
        if walkable(g, (i, -1)):
            t[i][-1].count = t[i + 1][-1].count
            t[i][-1].value = g[i][-1] + t[i + 1][-1].value

    if diag:
        for i in reversed(range(rows - 1)):
            for j in reversed(range(cols - 1)):
                if walkable(g, (i, j)):
                    neighbors = [t[i][j + 1], t[i + 1][j], t[i + 1][j + 1]]
                    maxvalue = max(neighbors, key=lambda x: x.value).value
                    t[i][j].count = sum(map(lambda x: x.count,
                                            filter(lambda x: x.value == maxvalue, neighbors)))
                    t[i][j].value = g[i][j] + maxvalue

    else:
        for i in reversed(range(rows - 1)):
            for j in reversed(range(cols - 1)):
                if walkable(g, (i, j)):
                    neighbors = [t[i][j + 1], t[i + 1][j]]
                    maxvalue = max(neighbors, key=lambda x: x.value).value
                    t[i][j].count = sum(map(lambda x: x.count,
                                            filter(lambda x: x.value == maxvalue, neighbors)))
                    t[i][j].value = g[i][j] + maxvalue

    return as_tuple_matrix(t)


def as_tuple_matrix(table: _Mat[NumOptCell]) -> _Mat[Tuple[int, int]]:
    return [[(x.count, x.value) for x in row] for row in table]


def build_opt_path(dptable: _Mat, diag: bool = False) -> List[_Cell]:
    # TODO: is it actually required if we also need to compute all optimal paths?
    assert dptable is not None

    ROWS, COLS = len(dptable), len(dptable[0])
    FULL_PATH_LEN = ROWS + COLS - 1
    path = []
    row, col = 0, 0

    # TODO: simplify edge cases by adding unwalkable border at edges?
    # if diag:
    #     while len(path) < FULL_PATH_LEN:
    #         pass

    # else:
    #     while len(path) < FULL_PATH_LEN:
    #         pass

    return path


def build_all_opt_path(f: _Mat[int], dptable: _Mat, diag: bool = False) -> _Mat[_Cell]:
    assert f is not None
    assert dptable is not None
    assert shape(f) == shape(dptable)

    rows, cols = shape(f)
    paths = []

    def _build_exclude_diag(path: List[_Cell]):
        if (cell := path[-1]) != (rows - 1, cols - 1):  # not last cell
            row, col = cell
            value_on_opt_path = dptable[row][col] - f[row][col]
            if row < (rows - 1):  # check the cell in the next row
                if dptable[row + 1][col] == value_on_opt_path:
                    _build_exclude_diag(path + [(row + 1, col)])

            if col < (cols - 1):  # check the cell in the next column
                if dptable[row][col + 1] == value_on_opt_path:
                    _build_exclude_diag(path + [(row, col + 1)])
        else:
            paths.append(path)

    def _build_include_diag(path: List[_Cell]):
        if (cell := path[-1]) != (rows - 1, cols - 1):  # not last cell
            row, col = cell
            value_on_opt_path = dptable[row][col] - f[row][col]
            if row < (rows - 1):  # check the cell in the next row
                if dptable[row + 1][col] == value_on_opt_path:
                    _build_include_diag(path + [(row + 1, col)])

            if col < (cols - 1):  # check the cell in the next column
                if dptable[row][col + 1] == value_on_opt_path:
                    _build_include_diag(path + [(row, col + 1)])

            if row < (rows - 1) and col < (cols - 1):
                if dptable[row + 1][col + 1] == value_on_opt_path:
                    _build_include_diag(path + [(row + 1, col + 1)])
        else:  # last cell, path is complete
            paths.append(path)

    if diag:
        _build_include_diag([(0, 0)])
    else:
        _build_exclude_diag([(0, 0)])
    return paths


def conceal(dptable: _Mat):
    """
    Conceals some cells of the table
    """
    # TODO: discuss how to select the cells to obfuscate
    cells = []
    for row, col in cells:
        dptable[row][col] = -1


def enforce_path_source(grid: _Mat, cell: _Cell) -> _Mat:
    assert grid is not None
    assert cell is not None
    assert check_contains_cell(grid, cell)

    rows, cols = shape(grid)
    cx, cy = cell
    out: Final = list(grid)

    # make all cells before the path source unwalkable
    for x in range(rows):
        for y in range(cols):
            if x < cx or y < cy:
                out[x][y] = _UNWALKABLE

    assert shape(out) == shape(grid)
    return grid


def enforce_path_target(grid: _Mat, cell: _Cell) -> _Mat:
    assert grid is not None
    assert cell is not None
    assert check_contains_cell(grid, cell)

    out: Final = list(grid)

    # make all cells after the path target unwalkable
    rows, cols = shape(grid)
    cx, cy = cell
    for x in range(rows):
        for y in range(cols):
            if x > cx or y > cy:
                out[x][y] = _UNWALKABLE

    assert shape(out) == shape(grid)
    return grid


def enforce_path_through(grid: _Mat, cell: _Cell) -> _Mat:
    """
    Create a copy of a grid that enforces the constraint of
    having all valid solution pass through a specific cell.

    Returns:
        a new grid which incorporates the constraint
    """
    assert grid is not None
    assert cell is not None
    assert check_contains_cell(grid, cell)

    rows, cols = len(grid[0]), len(grid)
    tx, ty = cell

    out = list(grid)
    # make lower-left corner unwalkable
    for x in range(0, tx):
        for y in range(ty + 1, rows):
            out[x][y] = _UNWALKABLE

    # make upper-right corner unwalkable
    for x in range(tx + 1, cols):
        for y in range(0, ty):
            out[x][y] = _UNWALKABLE

    assert shape(grid) == shape(out)
    return out


def splitgrids(g: _Mat, source: _Cell, through: _Cell, target: _Cell) -> Tuple[_Mat, _Mat]:
    """
    Simplify the task as a pair of grid problems:
        1. subgrid from 'cell_from' to 'cell_through'
        2. subgrid from 'cell_through' to 'cell_to'

    Returns:
        the top-left and the bottom-right subgrids
    """

    top_left_slice = [g[x][y] for x in range(source[0], through[0] + 1)
                      for y in range(source[1], through[1] + 1)]

    # through cell creates a chokepoint in the grid
    bottom_right_slice = [g[x][y] for x in range(through[0], target[0] + 1)
                          for y in range(through[1], target[1] + 1)]

    return top_left_slice, bottom_right_slice


def fusegrids(tl_slice: _Mat, br_slice: _Mat) -> _Mat:
    """
    Fills a full size grid

    Args:
        tl_slice: top-left subgrid, from 'cell_from' to 'cell_through
        br_slice: bottom-right subgrig, from 'cell_through' to 'cell_to'
    """
    assert check_matrix_shape(tl_slice)
    assert check_matrix_shape(br_slice)

    rows, cols = shape(grid)
    table = [[0 for _ in range(cols)] for _ in range(rows)]

    # place each subgrid in appropriate spot
    margins = [(source, through), (through, target)]
    for subgrid, cellmin, cellmax in zip([tl_slice, br_slice], margins):
        rows, cols = len(subgrid), len(subgrid[0])
        assert rows == cellmax[0] - cellmin[0]
        assert cols == cellmax[1] - cellmin[1]

        # copy over dptable
        for x in range(rows):
            for y in range(cols):
                table[cellmin[0] + x][cellmin[1] + y] = subgrid[x][y]

    return table


def solver(input_to_oracle):
    assert input_to_oracle is not None
    # _LOGGER.debug("input = %s", input_to_oracle)
    instance: Final[dict] = input_to_oracle["input_data_assigned"]
    print(input_to_oracle)

    # extract and parse inputs
    grid: Final = instance["grid"]
    diag: Final = instance["diag"]
    budget: Final = instance["budget"]
    source: Final = parse_cell(instance["cell_from"])
    target: Final = parse_cell(instance["cell_to"])
    through: Final = parse_cell(instance["cell_through"])

    print("from", source, "through", through, "to", target)
    problem = enforce_path_source(grid, source)
    print("problem", *problem, sep="\n")
    problem = enforce_path_target(problem, target)
    print("problem", *problem, sep="\n")
    problem = enforce_path_through(problem, through)
    print("problem", *problem, sep="\n")

    # top-left subgrid, bottom-right subgrid
    # subtables = [[f(g, diag=diag) for g in splitgrids(grid)] for f in [
    #     dptable_num_to,
    #     dptable_num_from,
    #     dptable_opt_to,
    #     dptable_opt_from,
    #     dptable_num_opt_to,
    #     dptable_num_opt_from]]

    # (DPtable_num_to, DPtable_num_from,
    #  DPtable_opt_to, DPtable_opt_from,
    #  DPtable_num_opt_to, DPtable_num_opt_from) = [fusegrids(*t) for t in subtables]

    DPtable_num_to = dptable_num_to(problem, budget, diag=diag)
    DPtable_num_from = dptable_num_from(problem, budget, diag=diag)

    DPtable_opt_to = dptable_opt_to(problem, budget, diag=diag)
    DPtable_opt_from = dptable_opt_from(problem, budget, diag=diag)

    DPtable_num_opt_to = dptable_num_opt_to(problem, budget, diag=diag)
    DPtable_num_opt_from = dptable_num_opt_from(problem, budget, diag=diag)

    # retrieve and format outputs
    # TODO: adapt solutions to different 'from' and 'to' cells
    num_paths = DPtable_num_to[-1][-1]
    num_opt_paths = DPtable_num_opt_to[-1][-1]
    opt_val = DPtable_opt_to[-1][-1]
    list_opt_paths = build_all_opt_path(grid, DPtable_opt_from, diag=diag)
    opt_path = list_opt_paths[0] if len(list_opt_paths) > 0 else []

    oracle_answers = {}
    for std_name, ad_hoc_name in input_to_oracle["request"].items():
        oracle_answers[ad_hoc_name] = locals()[std_name]
    return oracle_answers


class verify_submission_problem_specific(verify_submission_gen):
    def __init__(self, SEF,input_data_assigned:Dict, long_answer_dict:Dict):#, request_setups:Dict):
        super().__init__(SEF,input_data_assigned, long_answer_dict)#, request_setups)

    def verify_format(self, SEF):
        if not super().verify_format(SEF):
            return False
        if 'opt_val' in self.goals:
            g = self.goals['opt_val']
            if type(g.answ) != int:
                return SEF.format_NO(g, f"Come `{g.alias}` hai immesso `{g.answ}` dove era invece richiesto di immettere un intero.")
            SEF.format_OK(g, f"come `{g.alias}` hai immesso un intero come richiesto", f"ovviamente durante lo svolgimento dell'esame non posso dirti se l'intero immesso sia poi la risposta corretta, ma il formato è corretto")            
        if 'num_opt_sols' in self.goals:
            g = self.goals['num_opt_sols']
            if type(g.answ) != int:
                return SEF.format_NO(g, f"Come `{g.alias}` hai immesso `{g.answ}` dove era invece richiesto di immettere un intero.")
            SEF.format_OK(g, f"come `{g.alias}` hai immesso un intero come richiesto", f"ovviamente durante lo svolgimento dell'esame non posso dirti se l'intero immesso sia poi la risposta corretta, ma il formato è corretto")            
        if 'opt_sol' in self.goals:
            g = self.goals['opt_sol']
            if type(g.answ) != list:
                return SEF.format_NO(g, f"Come `{g.alias}` è richiesto si inserisca una lista di oggetti (esempio ['{self.I.labels[0]}','{self.I.labels[2]}']). Hai invece immesso `{g.answ}`.")
            for ele in g.answ:
                if ele not in self.I.labels:
                    return SEF.format_NO(g, f"Ogni oggetto che collochi nella lista `{g.alias}` deve essere uno degli elementi disponibili. L'elemento `{ele}` da tè inserito non è tra questi. Gli oggetti disponibili sono {self.I.labels}.")
            SEF.format_OK(g, f"come `{g.alias}` hai immesso un sottoinsieme degli oggetti dell'istanza originale", f"resta da stabilire l'ammissibilità di `{g.alias}`")
        return True
                
    def set_up_and_cash_handy_data(self):
        if 'opt_sol' in self.goals:
            self.sum_vals = sum([val for ele,cost,val in zip(self.I.labels,self.I.costs,self.I.vals) if ele in self.goals['opt_sol'].answ])
            self.sum_costs = sum([cost for ele,cost,val in zip(self.I.labels,self.I.costs,self.I.vals) if ele in self.goals['opt_sol'].answ])
            
    def verify_feasibility(self, SEF):
        if not super().verify_feasibility(SEF):
            return False
        if 'opt_sol' in self.goals:
            g = self.goals['opt_sol']
            for ele in g.answ:
                if ele in self.I.forced_out:
                    return SEF.feasibility_NO(g, f"L'oggetto `{ele}` da tè inserito nella lista `{g.alias}` è tra quelli proibiti. Gli oggetti proibiti per la Richiesta {str(SEF.task_number)}, sono {self.I.forced_out}.")
            for ele in self.I.forced_in:
                if ele not in g.answ:
                    return SEF.feasibility_NO(g, f"Nella lista `{g.alias}` hai dimenticato di inserire l'oggetto `{ele}` che invece è forzato. Gli oggetti forzati per la Richiesta {str(SEF.task_number)} sono {self.I.forced_in}.")
            if self.sum_costs > self.I.Knapsack_Capacity:
                return SEF.feasibility_NO(g, f"La tua soluzione in `{g.alias}` ha costo {self.sum_costs} > Knapsack_Capacity e quindi NON è ammissibile in quanto fora il budget per la Richiesta {str(SEF.task_number)}. La soluzione da tè inserita ricomprende il sottoinsieme di oggetti `{g.alias}`= {g.answ}.")
            SEF.feasibility_OK(g, f"come `{g.alias}` hai immesso un sottoinsieme degli oggetti dell'istanza originale", f"resta da stabilire l'ottimalità di `{g.alias}`")
        return True
                
    def verify_consistency(self, SEF):
        if not super().verify_consistency(SEF):
            return False
        if 'opt_val' in self.goals and 'opt_sol' in self.goals:
            g_val = self.goals['opt_val']; g_sol = self.goals['opt_sol'];
            if self.sum_vals != g_val.answ:
                return SEF.consistency_NO(['opt_val','opt_sol'], f"Il valore totale della soluzione immessa in `{g_sol.alias}` è {self.sum_vals}, non {g_val.answ} come hai invece immesso in `{g_val.alias}`. La soluzione (ammissibile) che hai immesso è `{g_sol.alias}`={g_sol.answ}.")
            SEF.consistency_OK(['opt_val','opt_sol'], f"{g_val.alias}={g_val.answ} = somma dei valori sugli oggetti in `{g_sol.alias}`.", "")
        return True
