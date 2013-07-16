__author__ = 'Ethan_Post'

import tkinter as tk
from debug import *
from bin import *
import os
import keyboard
import statusbox
import modalinputbox

def get_timeline_item_options_template ():
    template="""

# List of folders to display in the file bar. Separate each folder with a comma.
# folders=C:\temp, D:\temp\foo

# List of files to display in the file bar. Separate each file with a comma.
# files=C:\temp\foo.txt, C:\temp\random.doc

"""
    return template

class Item():
    def __init__(self, key):
        None

    def update_status(self,text):
        self.status.insert(0, to_char(datetime.now(), '%a %b %d %I:%M %p') + ' ' + text)
        self._status=text

    def add_tags(self, tags=None):
        """
        Append a single tag or extend the tag list with multiple tags in a list.
        """
        if type(tags)==list:
            self.tags.extend(tags)
        else:
            self.tags.append(tags)

    def dict(self):
        return {
            'key': self.key,
            'title': self.title,
            'image_path': self.image_path,
            'datetime': self.datetime,
            'state': self.state,
            'status': self.status,
            '_status': self._status,
            'size': self.size,
            'type': self.type,
            'shape': self.shape,
            'x': self.x,
            'y': self.y,
            'y_as_pct_of_height': self.y_as_pct_of_height,
            'tags': self.tags
        }

    def _parse_input_text(self, text):
            """
            Take the input text and parse out tags, title and current status.

            Title <status> [tag, tag]
            tag@Title <status> [tag,tag]

            """
            debug('Item._parse_input_text: {}'.format(text))

            # Values before the first '@' are tags and should be in a comma separated list
            # Some tags are special, like colors, only the first color will apply.

            self.tags=[]
            if text.find('@') > 0:
                at_tag=False
                tag=text.split('@')[0].strip()
                if ' ' not in tag:
                    at_tag=True
                    self.add_tags(tag)
                    text=text.split('@')[1]
                    
            debug('! tags={0} text={1}'.format(self.tags, text))

            # Status is in last set of angle brackets if it exist.
            if text.rfind('<') > 0:
                b=text.rfind('<')
                e=text.rfind('>')
                if b < e:
                    self.update_status(text[b+1:e])
                    text=text[0:b]+text[e+1:]

            debug('! status={0} text={1}'.format(self.status, text))

            # Everything in last set of brackets are tags.
            if text.rfind('['):
                b=text.rfind('[')
                e=text.rfind(']')
                if b < e:
                    are_tags=True
                    tags=text[b+1:e].split(',')
                    tags=[tag.strip() for tag in tags]
                    for tag in tags:
                        if ' ' in tag:
                            # Tags with blanks are not valid. These are probably not tags.
                            are_tags=False
                    if are_tags:
                        self.add_tags(tags)
                        text=text[0:b]+text[e+1:]

            debug('! tags={0} text={1}'.format(self.tags, text))

            self.title=text

class NewItem(Item):
    def __init__(self, text, x, y):
        self.key=random_string(20)
        self.title=None
        self.x=x
        self.y=y
        self.image_path=None
        self.state='initialized'
        self.status=[]
        self._status=''
        self.size=None
        self.shape='rectangle'
        self.type=None
        self.datetime=None
        self.y_as_pct_of_height=None
        self.tags=[]
        self._parse_input_text(text)

class Items():
    def __init__(self, *args, **kwargs):
        self.items=open_database('TIMELINE_ITEMS')

    def keys(self):
        return self.items.keys()

    def add_item(self, text, x, y, save=True):
        item=NewItem(text=text, x=x, y=y)
        self.items[item.key]=item.dict()
        if save:
            self.save()
        return item.key

    def delete_item(self, key, save=True):
        """
        Delete an item.
        """
        del self.items[key]
        if save:
            self.save()

    def update_item(self, key, save=True, **kwargs):
        debug('Items.update_item')
        item=self.items[key]
        for arg in kwargs.keys():
            if arg=='status':
                item['status'].insert(0, to_char(datetime.now(), '%a %b %d %I:%M %p') + ' ' + kwargs[arg])
                item['_status']=kwargs[arg]
            elif arg in item.keys():
                item[arg]=kwargs[arg]

        if save:
            self.save()
        
    def save(self):
        debug('Items.save')
        save_database('TIMELINE_ITEMS', self.items)

        
class Timeline():

    # Callback identifiers.
    DRAG_AND_DROP=7000
    CANCEL_DRAG_AND_DROP=7001
    ADD_ITEM_TO_TIMELINE=7002
    OPEN_TASK_FROM_TIMELINE=7003
    DELETE_ITEM_FROM_TIMELINE=7004
      
    def __init__(self, *args, **kwargs):

        debug('Timeline: kwargs={}'.format(kwargs))

        self.root=kwargs['root']
        self.canvas=kwargs['canvas']

        self.schemes={}

        self.schemes['default']={
            'name':'default',
            'background-color':'white',
            'line-color':'dark grey',
            'font-color':'black',
            'item-color':'blue',
            'item-outline-color': 'black',
            'item-active-fill':'white',
            'middle-line-color':'blue',
            'current-time-color': 'red',
            'font': ("Arial", 11),
            'label-font': ("Arial", 8),
            'item-size': 10
        }

        self.schemes['disabled']={
            'name':'disabled',
            'background-color':'white',
            'line-color':'light grey',
            'font-color':'dark grey',
            'item-color':'blue',
            'item-outline-color': 'white',
            'item-active-fill':'white',
            'middle-line-color':'white',
            'current-time-color': 'white',
            'font': ("Arial", 11),
            'item-size': 10,
            'label-font': ("Arial", 8),
        }

        self.scheme=self.schemes['default']

        if 'keyboard' in kwargs.keys():
            self.keyboard=kwargs['keyboard']
        else:
            self.keyboard=keyboard.Keyboard(canvas=self.canvas, cbfunc=(lambda dict: self.keypress(dict)))

        if 'width' in kwargs.keys():
            self.width=kwargs['width']
        else:
            self.width=self.canvas.winfo_reqwidth()
            
        if 'height' in kwargs.keys():
            self.height=kwargs['height']
        else:
            self.height=(100,90,80)
        
        if 'statusbox' in kwargs.keys():
            self.statusbox=kwargs['statusbox']
        else:
            self.statusbox=statusbox.StatusBox(
            root=self.root,
            canvas=self.canvas,
            x=2,
            y=2,
            height=16,
            width=self.width)

        if 'default_item_type' in kwargs.keys():
           self.default_item_type=kwargs['default_item_type']
        else:
           self.default_item_type=None

        if 'default_item_shape' in kwargs.keys():
           self.default_item_type=kwargs['default_item_shape']
        else:
           self.default_item_shape='rectangle'

        self.x=0
        self.y=0
        
        # Possible values are none, name, status
        self._item_label_display_state='none'

        # Stores information during drag and drop operations.
        self._dragging={}

        self.thumbnails={}
        
        self.timeline_time=None
        
        # Use object_id to return the key which was used to add the item (add_item).
        self._map_object_id_to_item_key={}

        if 'cbfunc' in kwargs.keys():
            self.cbfunc=kwargs['cbfunc']
        else:
            self.cbfunc=None

        self.canvas.focus_set()

        self.canvas.tag_bind("timelines", "<ButtonPress-1>",   self._timeline_mouse_click)
        self.canvas.tag_bind("timelines", "<B1-Motion>",       self._timeline_mouse_drag)
        self.canvas.tag_bind("timelines", "<Motion>",          self._timeline_mouse_motion)
        self.canvas.tag_bind("timelines", "<ButtonRelease-1>", self._timeline_mouse_up)
        self.canvas.tag_bind("timelines", "<Double-1>",        self._timeline_mouse_doubleclick)

        self.canvas.tag_bind("item", "<ButtonPress-1>",   self._item_mouse_down)
        self.canvas.tag_bind("item", "<B1-Motion>",       self._item_mouse_drag)
        self.canvas.tag_bind("item", "<Motion>",          self._item_mouse_over)
        self.canvas.tag_bind("item", "<ButtonRelease-1>", self._item_mouse_up)
        self.canvas.tag_bind("item", "<Double-1>",        self._item_mouse_doubleclick)
        self.canvas.tag_bind("item", "<Button-3>",        self._show_item_menu)

        self.hourly={
            'name': 'hourly',
            'y': self.y,
            'height': self.height[0],
            'total_days': .66
        }
        self.hourly['begin_time']=datetime.now()-timedelta(days=self.hourly['total_days']/2)
        self.hourly['label_format']='%I%p'

        self.daily={
            'name': 'daily',
            'y': self.hourly['y']+self.hourly['height'],
            'height': self.height[1],
            'total_days': 14
        }
        self.daily['begin_time']=datetime.now()-timedelta(days=self.daily['total_days']/2)
        self.daily['label_format']='%d%a'

        self.monthly={
            'name': 'monthly',
            'y': self.daily['y']+self.daily['height'],
            'height': self.height[2],
            'total_days': 120
        }
        self.monthly['begin_time']=datetime.now()-timedelta(days=self.monthly['total_days']/2)
        self.monthly['label_format']='%B %y'

        self.timelines=(self.hourly, self.daily, self.monthly)

        self._timelines_draw()

        # This is a dict of all of the items in the database, indexed by key.
        self.timeline_items=Items()

        self.patch()

        self.draw_items()

        # Just a temporary dict which we can use for this and that.
        self.temp={}

        self._build_menus()

    def _build_menus(self):
        debug('Timeline._build_menus')
        self.menu=tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="Status", command=self._set_status_text_for_item)
        self.menu.add_separator()
        self.menu.add_command(label="Rename", command=self._open_item_rename_form)



    def _clear_display(self):
        debug2('Timeline._display_clear')
        if self.statusbox:
            self.statusbox.clear()
        
    def delete_item_from_timeline(self, key):
        debug('Timeline.delete_item_from_timeline')
        self.timeline_items.delete_item(key, save=True)
        self.draw_items()
        if self.cbfunc:
            self.cbfunc({'cbkey': self.DELETE_ITEM_FROM_TIMELINE, 'key': key})

    def _display_time_with_text(self, time, text=None):
        debug2('Timeline._display_time_with_text')
        if time and text:
            self._display_text('{0} {1}'.format(to_char(time, '%a %b %d %I:%M %p'), text))
        elif time and not text:
            self._display_text('{0}'.format(to_char(time, '%a %b %d %I:%M %p')))
        else:
            self.statusbox.clear()

    def _display_text(self, text):
        debug2('Timeline._display_text')
        if self.statusbox:
            self.statusbox.clear()
            self.statusbox.set_text(text)

    def draw_items(self):
        debug('Timeline.draw_items')
        self.canvas.delete('all_items_and_labels')
        self._map_object_id_to_item_key={}
        for key in self.timeline_items.keys():
            self.draw_item(key, delete_first=False)

    def draw_item(self, key, delete_first=True):
        debug2('Timeline.draw_item: key={}'.format(key))

        item=self.timeline_items.items[key]

        if item['state']=='initialized':
            item['datetime']=self._get_time_from_xy(item['x'], item['y'])
            item['y_as_pct_of_height']=self._get_y_as_pct_of_height_from_xy(item['x'], item['y'])
            if not item['size']:
                item['size']=int(self.height[0]/10)
            item['state']='open'
            self.timeline_items.save()

        if delete_first:
            self.canvas.delete(key)

        item_tags='all_items_and_labels item drags ' + key
        label_tags='all_items_and_labels ' + key
            
        for timeline in self.timelines:
            if item['datetime'] >= timeline['begin_time'] and item['datetime'] <= timeline['end_time']:
                
                if timeline['name']=="hourly":
                    size=item['size']
                elif timeline['name']=="daily":
                    size=int(item['size']*.8)
                elif timeline['name']=="monthly":
                    size=int(item['size']*.8*.8)

                if self.scheme['name']=='disabled':
                    item_color=self.scheme['item-color']
                else:
                    item_color='blue'

                x=days_between_two_dates(item['datetime'], timeline['begin_time'])/timeline['total_days']*self.width
                y=timeline['y']+(timeline['height']*item['y_as_pct_of_height'])
                if item['shape']:
                    if item['shape']=='rectangle':
                        object_id=self.canvas.create_rectangle(x, y, x+size, y+size, fill=item_color, outline='black', tags=item_tags, stipple=None, activefill='black')
                    else:
                        critical('ERROR! Item shape not recognized!')
                else:
                    if item['image_path']:
                        thumb_key='{0}_{1}'.format(item['key'], timeline['name'])
                        if thumb_key not in self.thumbnails.keys():
                            thumbnail=get_photoimage_thumbnail(item['file_path'], border_color='black', border_size=1, size=size)
                            self.thumbnails[thumb_key]=thumbnail
                        object_id=self.canvas.create_image(x, y, anchor=tk.NW, image=self.thumbnails[thumb_key], state=tk.NORMAL, tags=item_tags)
                    else:
                        critical('ERROR: image_path not defined!')
                        
                # Keep a reference so we can get a key using the object ID easily.

                debug('object_id {0} is mapped to key {1}'.format(object_id, key))
                self._map_object_id_to_item_key[object_id]=key

                # Draw labels for hourly timeline.
                # ToDo: This is going to break for images.
                if (timeline['name']=="hourly" and self._item_label_display_state != 'none'):
                    if self._item_label_display_state=='title':
                        display_text=item['title']
                    else:
                        display_text='[' + item['_status'] + ']'
                    x,y,right,bottom=self.canvas.coords(object_id)
                    object_id=self.canvas.create_text(right+5, y-2, text=display_text, font=("Arial", 8), fill="black", tags=label_tags, anchor="nw", justify="left")

    def _get_closest_object_id_from_xy_with_tag(self, x, y, tag, start=0):
        object_id=self.canvas.find_closest(x, y, start=start)[0]
        if tag in self.canvas.gettags(object_id):
            return object_id

    def _get_x_from_time(self, datetime_object, begin_time, total_days, width):
        r=days_between_two_dates(datetime_object, begin_time)/total_days*width
        return r

    def _get_next_month(self, datetime_object):
        r=datetime_object.replace(day=28)+timedelta(days=4)
        #debug("get_next_month: r={0}".format(r))
        r=r.replace(day=1)
        #debug("get_next_month: r={0}".format(r))
        return r

    def _get_item_key_from_object_id(self, object_id):
        debug('Timeline._get_item_key_from_object_id: {}'.format(object_id))
        return self._map_object_id_to_item_key[object_id]

    def _get_item_from_xy(self, x, y):
        for o in self.canvas.find_overlapping(x, y, x+1, y+1):
            if 'foo' in self.canvas.gettags(o):
                debug('item found!')

    def _get_status_text(self, item):
       if item['_status']:
           return '[{}]'.format(item['_status'])
       else:
           return None

    def _get_title_and_status_text(self, item):
       if item['_status']:
           return '{0} [{1}]'.format(item['title'], item['_status'])
       else:
           return item['title']

    def _get_time_from_xy(self, x, y):
        debug("_get_time_from_item: x={0} y={1}".format(x, y))
        timeline=self._get_timeline_from_xy(x, y)
        if timeline:
            return timeline['begin_time']+timedelta(days=x/self.width*timeline['total_days'])
        else:
            return None

    def _get_timeline_from_xy(self, x, y):
        debug('_get_timeline_from_item: x={0} y={1}'.format(x, y))
        for t in self.timelines:
            if x > self.x and x < t['right'] and y > t['y'] and y < t['bottom']:
                return t

    def _get_y_as_pct_of_height_from_xy(self, x, y):
        timeline=self._get_timeline_from_xy(x, y)
        y_as_pct_of_height=abs(y-timeline['y'])/timeline['height']
        return y_as_pct_of_height

    def _is_item_being_dragged (self):
        return 'object_id' in self._dragging
    
    def keypress(self, dict):
        debug('Timeline.keypress: {}'.format(dict))
        
        # F1 key press
        if dict['state']==8 and dict['keycode']==112:
            map={
                'none':'title',
                'title':'status',
                'status':'none'
            }
            self._item_label_display_state=map[self._item_label_display_state]

            # ToDo: To speed performance up here I cold just draw the hourly items.
            self.draw_items()

    def link_statusbox_to_timeline(self, statusbox):
        self.statusbox=statusbox
        
    def _item_mouse_down(self, event):
        debug2('_item_mouse_down: x={0} y={1}'.format(event.x, event.y))
        # event.x and event.y are the based on the item of the cursor. not the object being clicked.
        object_id=self._get_closest_object_id_from_xy_with_tag(event.x, event.y, 'item')
        if self.keyboard.escape_key_down:
            self.delete_item_from_timeline(self._get_item_key_from_object_id(object_id))

        if 'drags' in self.canvas.gettags(object_id):
            self._dragging['object_id']=object_id
            self.canvas.tag_raise(object_id)
            # Store the original position in case we need to abort the drag and drop.
            self._dragging['coords']=self.canvas.coords(object_id)
            self._dragging['x']=self._dragging['x0']=event.x
            self._dragging['y']=self._dragging['y0']=event.y



    def _item_mouse_over(self, event):
        debug2('Timeline._item_mouse_over')
        if not self._is_item_being_dragged():
            object_id=self._get_closest_object_id_from_xy_with_tag(event.x, event.y, 'item')
            if object_id:
                coords=self.canvas.coords(object_id)
                time=self._get_time_from_xy(coords[0], coords[1])
                timeline=self._get_timeline_from_xy(event.x, event.y)
                key=self._get_item_key_from_object_id(object_id)
                item=self.timeline_items.items[key]
                text=None
                if time and key:
                    if self._item_label_display_state=='none':
                        text=self._get_title_and_status_text(item)
                    elif self._item_label_display_state=='title':
                        text=self._get_status_text(item)
                    elif self._item_label_display_state=='status':
                        text=item['title']
                    self._display_time_with_text(time, text)
                else:
                    debug('No coord time!')
            else:
                debug('No object id!')

    def _item_mouse_drag(self, event):
        debug2('_item_mouse_drag')
        if 'object_id' in self._dragging:
            object_id=self._dragging['object_id']
            coords=self.canvas.coords(object_id)
            self._display_time_with_text(self._get_time_from_xy(coords[0], coords[1]))
            delta_x = event.x - self._dragging["x"]
            delta_y = event.y - self._dragging["y"]
            self._dragging["x"] = event.x
            self._dragging["y"] = event.y
            self.canvas.move(object_id, delta_x, delta_y)

    def _item_mouse_drag_abort(self, x, y):
        debug2('_item_mouse_drag_abort')
        self.canvas.coords(
            self._dragging['object_id'],
            self._dragging['coords'][0],
            self._dragging['coords'][1],
            self._dragging['coords'][2],
            self._dragging['coords'][3])

    def _item_mouse_up(self, event):
        debug2('_item_mouse_up')

        if 'object_id' not in self._dragging:
            return
        else:
            object_id=self._dragging['object_id']

        delta_x = event.x - self._dragging["x0"]
        delta_y = event.y - self._dragging["y0"]

        if delta_x != 0 or delta_y != 0:
            # Depending on object type coords call may return 2 or 4 items in tuple.
            coords=self.canvas.coords(object_id)
            x=coords[0]
            y=coords[1]
            item=self.timeline_items.items[self._get_item_key_from_object_id(object_id)]
            timeline=self._get_timeline_from_xy(x,y)
            if timeline:
                item['datetime']=self._get_time_from_xy(x,y)
                item['x']=x
                item['y_as_pct_of_height']=(y-timeline['y'])/timeline['height']
                del self._map_object_id_to_item_key[object_id]
                self.canvas.delete(item['key'])
                self.draw_item(item['key'])
                # Make sure we save changes to timeline database.
                self.timeline_items.save()
                if self.cbfunc and item['type'] != 'image':
                    self.cbfunc({'cbkey': self.DRAG_AND_DROP, 'item': item})
            else:
                self._item_mouse_drag_abort(event.x, event.y)
                if self.cbfunc:
                     # Add the x and y drop locations.
                    self.cbfunc({'cbkey': self.CANCEL_DRAG_AND_DROP, 'item': item, 'x':x, 'y':y})

        self._dragging={}
        self._clear_display()

    def _item_mouse_doubleclick(self, event):
        debug2('_item_mouse_doubleclick')
        object_id=self._get_closest_object_id_from_xy_with_tag(event.x, event.y, 'item')
        key=self._get_item_key_from_object_id(object_id)
        form=modalinputbox.ModalInputBox(
            root=self.root,
            canvas=self.canvas,
            text=self.timeline_items.items[key]['title'])
        if form.text:
            self.update_item(key, name=form.text)
            self.draw_item(key)
        self.canvas.focus_force()

    def _open_item_rename_form(self):
        debug('_rename_item')
        object_id=self.temp['object_id']
        key=self._get_item_key_from_object_id(object_id)
        form=modalinputbox.ModalInputBox(
            root=self.root,
            canvas=self.canvas,
            text=self.timeline_items.items[key]['title'])
        if form.text:
            self.timeline_items.update_item(key, title=form.text)
            self.draw_item(key)
        self.canvas.focus_force()

    def _object_is_item(self, object_id):
        if 'item' in self.canvas.gettags(object_id):
            return True
        else:
            return False

    def patch(self):
        None

    def remove_item(self, key):
        debug('Timeline.remove_item')
        self.timeline_items.delete_item(key=key, save=True)
        self.draw_items()

    def _save_timeline_begin_times(self):
        self.hourly['dragging_begin_time']=self.hourly['begin_time']
        self.daily['dragging_begin_time']=self.daily['begin_time']
        self.monthly['dragging_begin_time']=self.monthly['begin_time']

    def _set_status_text_for_item(self):
        debug('_add_item_status')
        if self.temp['object_id']:
            object_id=self.temp['object_id']
            key=self._get_item_key_from_object_id(object_id)
            form=modalinputbox.ModalInputBox(
                root=self.root,
                canvas=self.canvas,
                text='')
            if form.text:
                self.timeline_items.update_item(key, status=form.text)
                self.draw_item(key)
            self.canvas.focus_force()

    def _set_first_label_time(self):
        """
        Calculates the time of the first label for each timeline using the current begin_time.
        """
        self.hourly['first_label']=self.hourly['begin_time'].replace(minute=0, second=0, microsecond=0)
        self.daily['first_label']=self.daily['begin_time'].replace(hour=0, minute=0, second=0, microsecond=0)
        self.monthly['first_label']=self.monthly['begin_time'].replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def _show_item_menu(self, event):
        debug('Timeline._show_item_menu')
        object_id=self._get_closest_object_id_from_xy_with_tag(event.x, event.y, 'item')
        if self._object_is_item(object_id):
            self.temp['object_id']=object_id
            x=self.canvas.winfo_rootx()+event.x
            y=self.canvas.winfo_rooty()+event.y
            self.menu.post(x+15, y)

    def _timeline_mouse_click(self, event):
        debug('_timeline_mouse_click')
        # Determine which timeline was clicked on.
        t=self._get_timeline_from_xy(event.x, event.y)

        if self.keyboard.shift_key_down:
            self.keyboard.shift_key_down=False
            self._timeline_mouse_click_add_item(event.x, event.y)
        else:
            self._save_timeline_begin_times()

            if t:
                self._dragging['timeline']=t
                # Required in order to capture keypress events.
                self.canvas.focus_set()
                debug('timeline={}'.format(t))
            else:
                self._dragging={}
                critical('ERROR: Could not locate a timeline on mouse down click!')
            # Need a reference to the original mouse down item.
            self._dragging['x']=event.x

    def _timeline_mouse_click_add_item(self, x, y):
        # Need to save the x and y position. When the item is saved we will need to refer to this.
        timeline=self._get_timeline_from_xy(x, y)
        if timeline:
            self._timelines_disable()
            form=modalinputbox.ModalInputBox(
                root=self.root,
                canvas=self.canvas,
                text=''
            )
            if form.text:
                key=self.timeline_items.add_item(text=form.text, x=x, y=y, save=True)
                self.timeline_items.save()
                self.draw_item(key)
                if self.cbfunc:
                    self.cbfunc({'cbkey': self.ADD_ITEM_TO_TIMELINE, 'item': self.timeline_items[key]})
            self._timelines_enable()
            self.canvas.focus_force()

    def _timeline_mouse_doubleclick(self, event):
        debug2('_timeline_mouse_doubleclick')
        t=self._get_time_from_xy(event.x, event.y)
        for timeline in self.timelines:
            timeline['begin_time']=t-timedelta(days=timeline['total_days']/2)
            self._timelines_draw_details()

    def _timeline_mouse_motion(self, event):
        if self.keyboard.shift_key_down:
            self._display_time_with_text(self._get_time_from_xy(event.x, event.y))
        else:
            self._clear_display()

    def _timeline_mouse_drag(self, event):
        debug2("_timeline_mouse_drag")

        if "timeline" not in self._dragging.keys():
            critical('timeline not in _dragging.keys!')
            return

        t=self._dragging['timeline']

        if t:
            x=event.x-self._dragging['x']
            if x==0:
                return

            days=x/self.width*t['total_days']*-1

            self.monthly['begin_time']=self.monthly['dragging_begin_time']+timedelta(days=days)
            self.daily['begin_time']=self.monthly['begin_time']+timedelta(days=self.monthly['total_days']/2)-timedelta(days=self.daily['total_days']/2)
            self.hourly['begin_time']=self.monthly['begin_time']+timedelta(days=self.monthly['total_days']/2)-timedelta(days=self.hourly['total_days']/2)

            self.timeline_time=self.monthly['begin_time']+timedelta(days=self.monthly['total_days']/2)
            self._display_time_with_text(self.timeline_time)

            self._timelines_draw_details()
            self.draw_items()
        else:
            critical('ERROR: timeline not found while dragging!')

    def _timeline_mouse_up(self, event):
        debug2("timeline_mouse_up")
        self.draw_items()
        self._dragging_timeline={}
        self._clear_display()

    def _timelines_draw(self):
        debug2('_timelines_draw')
        self.canvas.delete("timelines")
        for t in self.timelines:
            t['right']=self.x+self.width
            t['bottom']=t['y']+t['height']
            t['center_x']=self.x+(self.width/2)
            t['center_y']=t['y']+(t['height']/2)
            object_id=self.canvas.create_rectangle(self.x, t['y'], t['right'], t['bottom'], fill=self.scheme['background-color'], outline=self.scheme['line-color'], tags="timelines")
            self.canvas.tag_lower(object_id)
        self._timelines_draw_details()

    def _timelines_draw_details(self):
        debug2('_timelines_draw_details')
        self.canvas.delete("timeline_detail")
        # Recalculate the time of first label for each timeline using current begin_time.
        self._set_first_label_time()
        for t in self.timelines:
            t['end_time']=t['begin_time']+timedelta(days=t['total_days'])
            x=self._get_x_from_time(t['first_label'], t['begin_time'], t['total_days'], self.width)
            label_time=t['first_label']
            for i in range(1,100):
                l=to_char(label_time, t['label_format'])
                self.canvas.create_line(x, t['y'], x, t['bottom'], fill=self.scheme['line-color'], tags="timeline_detail")
                self.canvas.create_text(x+1,t['bottom']-8, font=self.scheme['label-font'], text=l, anchor="w", fill=self.scheme['font-color'], tags="timeline_detail")
                if t['name']=='hourly':
                    label_time=label_time+timedelta(hours=1)
                elif t['name']=='daily':
                    label_time=label_time+timedelta(hours=24)
                elif t['name']=='monthly':
                    label_time=self._get_next_month(label_time)
                x=self._get_x_from_time(label_time, t['begin_time'], t['total_days'], self.width)
                if label_time > t['begin_time']+timedelta(days=t['total_days']):
                    break

            # Draw red line in middle of timeline.
            x=self._get_x_from_time(t['begin_time']+timedelta(days=t['total_days']/2), t['begin_time'], t['total_days'], self.width)
            self.canvas.create_line(x, t['y'], x, t['y']+t['height'], fill=self.scheme['middle-line-color'], tags="timeline_detail")

            # Draw blue line at current time.
            x=self._get_x_from_time(datetime.now(), t['begin_time'], t['total_days'], self.width)
            self.canvas.create_line(x, t['y'], x, t['y']+t['height'], fill=self.scheme['current-time-color'], tags="timeline_detail")

    def _timelines_disable(self):
        self.scheme=self.schemes['disabled']
        self._timelines_draw()
        self.draw_items()

    def _timelines_enable(self):
        self.scheme=self.schemes['default']
        self._timelines_draw()
        self.draw_items()