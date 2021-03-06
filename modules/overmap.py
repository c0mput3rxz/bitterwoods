from mud.module import Module
from mud.inject import inject
from mud.collection import Collection, Entity, FileStorage

class Overmap(Collection):
    ENTITY_CLASS = Entity
    STORAGE_CLASS = FileStorage


@inject("Overmap", "Areas")
def overmaps_command(self, Areas, *args, **kwargs):
    # TO_DO Table-fy this.
    count = 0
    self.echo("Available Overmaps.")
    self.echo("{R+" + "-" * 78 + "+")
    self.echo("{w|Level    | Vis |  Name           |  Description")
    self.echo("{R" + "-" * 78 + "+")
    for area in Areas.query():
        if not area.area_map:
            continue
        else:
            self.echo(f"{{R|{{w{area.min_level:>3} - {area.max_level:>3}| {area.visibility:>3} | {area.name:^15} | {area.description:<}")
            count += 1
    self.echo("{R" + "-" * 78 + "+")
    self.echo(f"({count}) Overmap(s) found")


@inject("Areas", "Directions")
def overmaps_fly_command(self, Areas, Directions, *args, **kwargs,):
    args = kwargs.get("args")
    print(args)
    print(f"length {len(args)}")
    for area in Areas.query():
        if not area.area_map:
            continue
        else:
            if len(args) > 2 or len(args) == 1:
                self.echo("Usage: fly <1-5> <N|S|E|W|NE|NW|SE|SW>")
                raise TypeError('fly takes at most 2 positional '
                                'arguments (%d given)' % (len(args),))
            elif not args or len(args) == 0:
                if area.can_fly:
                    if self.overmap_fly:
                        self.echo("You fall to the ground.")
                        self.overmap_fly = False
                    else:
                        self.echo("You rise into the air.")
                        self.overmap_fly = True
                else:
                    self.echo("You can not seem to fly here.")
                    self.overmap_fly = False
            elif len(args) == 2:
                legal_size = '12345'
                legal_directions = 'nwsenesw'

                if args[0] not in legal_size or args[1] not in legal_directions:
                    self.echo("Usage: fly <1-5> <N|S|E|W|NE|NW|SE|SW>")
                else:
                    # self.echo(f"You attempt to fly...{args[0]} {args[1]}")
                    direction = Directions.fuzzy_get(args[1])
                    if not direction:
                        self.echo("Are you sure you know where we are going?.")
                        return
                    if not self.overmap_fly:
                        self.echo(f"You rise into the air... ")
                        self.overmap_fly = True
                    self.echo(f"You attempt to fly {direction.colored_name}")
                    overmap_walk(self, int(args[0]), direction)
            return
    self.echo("Area not found, where are you?!")


@inject("Areas")
def o_recall(self, area, *args, **kwargs):
    if not area.overmap_recall:
        set_actor_location(self, area, 1, 1)
    else:
        set_actor_location(self, area, area.overmap_recall[0], area.overmap_recall[1])


class OvermapModule(Module):
    DESCRIPTION = "Allow players to edit overmap."

    def __init__(self, game):
        super(OvermapModule, self).__init__(game)
        self.game.register_command("overmap_recall", o_recall)
        self.game.register_command("overmaps", overmaps_command)
        self.game.register_command("fly", overmaps_fly_command)
        self.game.register_injector(Overmap)


def set_actor_location(actor, area, new_x, new_y):
    print(new_x)
    print(new_y)
    actor.overmap_x = new_x
    actor.overmap_y = new_y
    actor.overmap = area.name
    actor.save()

    if not area.overmap_actors:
        area.overmap_actors = {}

    area.overmap_actors[actor.name] = (new_x, new_y)
    print(area.overmap_actors)
    area.save()
    # draw_room(actor, actor.overmap_x, actor.overmap_y, area)
    draw_map(actor, area)


def is_actor_at(x, y, area):
    if not area.overmap_actors:
        return False
    for loc in area.overmap_actors:
        if loc[0] == x and loc[1] == y:
            print("Found You")
            return True
    return False


def is_object_at(x, y, area):
    if not area.overmap_objects:
        return False
    for loc in area.overmap_objects.items():
        if loc[0] == x and loc[1] == y:
            return True
    return False


def is_room_at(x, y, area):
    if not area.overmap_rooms:
        return False
    for loc in area.overmap_rooms.items():
        if loc[0] == x and loc[1] == y:
            return True
    return False


def draw_room(self, x, y, area):
    if is_actor_at(x, y, area):
        return "{R*"
    if is_object_at(x, y, area):
        return "{G!"
    if is_room_at(x, y, area):
        return "{BV"

    # self.echo(area.color_mapping)
    return area.color_mapping[area.area_map[y][x]] + area.area_map[y][x]


def checkmove(area, x, y):
    if area.area_map[y][x] == '-' or area.area_map[y][x] == '-' or \
            area.area_map[y][x] == '+' or area.area_map[y][x] == '|':
        return False
    return True


def draw_map(self, area):

    # Find slice indexes for horizontal
    print(self.overmap_x)
    print(area.visibility)
    start_x = max(0, self.overmap_x - area.visibility - 1)
    end_x = min(area.width - 1, self.overmap_x + area.visibility) + 1

    # Find slice indexes for vertical
    start_y = max(0, self.overmap_y - area.visibility)
    end_y = min(area.height - 1, self.overmap_y + area.visibility) + 1

    # Slice region
    map_slice = [
        row[start_x:end_x] for row in area.area_map[start_y:end_y]
    ]

    xcount = 0
    ycount = 0
    # Draw
    self.echo(f"Area: {area.name}")
    for line in map_slice:
        map_line = f"[{{w{start_y + ycount - self.overmap_y:>3}]"
        for room in line:
            if self.overmap_x == xcount + start_x and self.overmap_y == ycount + start_y:
                map_line += "{R@"
            else:
                map_line += f"{draw_room(self, xcount + start_x, ycount + start_y, area)}"
            xcount += 1
        self.echo(map_line)
        xcount = 0
        ycount += 1
    self.echo(f"{{wLocation:  {self.overmap_x}.{self.overmap_y}")
    self.echo(f"Nearby: {self.name}")


@inject("Areas", "Directions")
def overmap_walk(self, step, direction, Areas, Directions):
    self.echo(f"Attempting to walk...{direction}")
    for area in Areas.query():
        if self.overmap == area.name:
            print(direction)
            new_x = self.overmap_x
            new_y = self.overmap_y
            if direction.id == "north":
                if self.overmap_y - step > 0:
                    new_y = new_y - step
                    # set_actor_location(self, area, self.overmap_x, self.overmap_y - 1)
                    # draw_map(self, area)
                else:
                    self.echo(f"You are at the northern boarder of {area.name}")
            if direction.id == "south":
                if self.overmap_y < area.height - step:
                    new_y = new_y + step
                    # set_actor_location(self, area, self.overmap_x, self.overmap_y + 1)
                    # draw_map(self, area)
                else:
                    self.echo(f"You are at the southern boarder of {area.name}")
            if direction.id == "east":
                if self.overmap_x < area.width - step:
                    new_x = new_x + step
                    # set_actor_location(self, area, self.overmap_x + 1, self.overmap_y)
                    # draw_map(self, area)
                else:
                    self.echo(f"You are at the eastern boarder of {area.name}")
            if direction.id == "west":
                if self.overmap_x - step> 0:
                    new_x = new_x - step
                    # set_actor_location(self, area, self.overmap_x - 1, self.overmap_y)
                    # draw_map(self, area)
                else:
                    self.echo(f"You are at the western boarder of {area.name}")
            if direction.id == "se":
                if self.overmap_x < area.width - step and self.overmap_y < area.height - step:
                    new_x = new_x + step
                    new_y = new_y + step
                    # set_actor_location(self, area, self.overmap_x + 1, self.overmap_y + 1)
                    # draw_map(self, area)
                else:
                    self.echo(f"You are at the boarder of {area.name}")
            if direction.id == "sw":
                if self.overmap_x - step > 0 and self.overmap_y < area.height - step:
                    new_x = new_x - step
                    new_y = new_y + step
                    # set_actor_location(self, area, self.overmap_x - 1, self.overmap_y + 1)
                    # draw_map(self, area)
                else:
                    self.echo(f"You are at the boarder of {area.name}")
            if direction.id == "ne":
                if self.overmap_x < area.width - step and self.overmap_y - step> 0:
                    new_x = new_x + step
                    new_y = new_y - step
                    # set_actor_location(self, area, self.overmap_x + 1, self.overmap_y - 1)
                    # draw_map(self, area)
                else:
                    self.echo(f"You are at the boarder of {area.name}")
            if direction.id == "nw":
                if self.overmap_x - step > 0 and self.overmap_y - step > 0:
                    new_x = new_x - step
                    new_y = new_y - step
                    # set_actor_location(self, area, self.overmap_x - 1, self.overmap_y - 1)
                    # draw_map(self, area)
                else:
                    self.echo(f"You are at the boarder of {area.name}")
            if new_x != self.overmap_x or new_y != self.overmap_y:
                if checkmove(area, new_x, new_y):
                    set_actor_location(self, area, new_x, new_y)
                    draw_map(self, area)
                else:
                    self.echo(f"Encountered a wall {direction.id} of here")
    # if direction == "up":
    # if direction == "down":

