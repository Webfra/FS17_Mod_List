import os
import re
import sys

import xml.etree.ElementTree as ET

from tiny_html import Tag, Html
from fs17 import Mod

# ============================================================================
SAVE_DIR = r'~\Documents\My Games\FarmingSimulator2017\mods'
'''Folder where the mods are installed to be used by the game.'''

GAME_DIR = r'D:\steam\steamapps\common\Farming Simulator 17'
'''Location where the game is installed.'''

MOD_VAULT = r'..\Mods'
'''Folder where the FS17 mods are stored as backup.'''

OUTPUT_FILE = '_FS7_Mod_List.html'
'''Name of the HTML file to create.

A leading underscore ensures it is listed first in Explorer.'''

HTML_TITLE = 'FS17 - Mod List'
'''The title of the HTML document.'''

# ============================================================================
# Constants for HTML generation.
# Size (width and height) of the icons in the HTML.
# All icons will be scaled (up or down) to this size.
IMG_SIZE = 128
'''The size, to which all Mod icons will be scaled to.'''


# ============================================================================
# main script function to create an HTML overview document of all Mods stored in a folder.
def main() -> None:
    # ------------------------------------------------------------------------
    # Get the list of installed Mods. (ZIP files only)
    save_dir = os.path.expanduser(SAVE_DIR)
    installed_mods = []
    if os.path.exists(save_dir):
        installed_mods = get_zipfiles(save_dir)
        # Remove folders from filenames.
        installed_mods = [os.path.basename(mod) for mod in installed_mods]

    # ------------------------------------------------------------------------
    # Get the list of Mods in the current folder.
    print('Finding Mods in', os.path.abspath(MOD_VAULT))
    list_of_zipfiles = get_zipfiles(MOD_VAULT)
    if len(list_of_zipfiles) <= 0:
        print('***ERROR: No Mods (ZIP files) found in:',
              os.path.abspath(MOD_VAULT))
        sys.exit(-1)

    # ------------------------------------------------------------------------
    mods = {}

    # ------------------------------------------------------------------------
    # Read MOD information and prepare HTML content.
    num_mods = len(list_of_zipfiles)
    print(f'Reading information for {num_mods} mods...')
    for _idx, zipfile in enumerate(list_of_zipfiles):
        # ------------------------------------------------------------------------
        # Show progress.
        print(_idx+1, 'of', len(list_of_zipfiles), zipfile)
        # ------------------------------------------------------------------------
        # Collect information about the mod.
        try:
            mod = Mod(zipfile, GAME_DIR, IMG_SIZE)
        except KeyError as e:
            print(f"\n***WARNING: Couldn't open file {zipfile}:")
            print(e)
            continue
        except ET.ParseError as e:
            print(
                f'\n***WARNING: Error opening modDesc.xml in file {zipfile}:')
            print(e)
            continue
        # ------------------------------------------------------------------------
        # Create a HTML representation for the mod.
        div, mod, icon, info, desc = create_mod_html(mod, installed_mods)
        # ------------------------------------------------------------------------
        # Determine Category from folder name.
        cat = os.path.dirname(zipfile)
        if cat != MOD_VAULT:
            cat = os.path.basename(cat)
        else:
            cat = 'None'
        # ------------------------------------------------------------------------
        mod_list = mods.setdefault(cat, {}).setdefault(mod.title.upper(), [])
        mod_list.append((div, mod, icon, info, desc))

    # ------------------------------------------------------------------------
    # Create the HTML document from the list of mods.
    doc = create_html_doc(mods)

    # ------------------------------------------------------------------------
    # Write the HTML document into the MOD_VAULT folder.
    out_file = os.path.abspath(os.path.join(MOD_VAULT, OUTPUT_FILE))
    print(f'Writing HTML file: {out_file} ...')
    doc.save(out_file)
    # ------------------------------------------------------------------------


# ============================================================================
def create_html_doc(mods: dict) -> Html:
    """Create a HTML document from the mods dictionary."""

    # ------------------------------------------------------------------------
    # Start a new HTML file.
    html = Html()
    # ------------------------------------------------------------------------
    # Create a <head> tag.
    html.head.tag('title', text=HTML_TITLE)
    with open('styles.css', 'rt') as css:
        html.head.tag('style', {'type': 'text/css'}, text=css.read())
    # ------------------------------------------------------------------------
    # Keep track of global mod number.
    mod_number = 0
    # ------------------------------------------------------------------------
    # Create a <body> tag.
    body = html.body
    body.tag('h1', {'class': 'fsgreen'}, text=HTML_TITLE)
    table = body.tag('table')
    # ------------------------------------------------------------------------
    # Hide categories row, if mods are stored in main folder. (e.g. no categories defined.)
    show_categories = not ((len(mods) <= 1) and ('None' in mods))
    # ------------------------------------------------------------------------
    all_cats = sorted(mods)[:]
    for cat in all_cats:
        # ------------------------------------------------------------------------
        m = re.match('\d+_(.*)', cat)
        vis_cat = m.group(1) if m else cat
        # ------------------------------------------------------------------------
        if show_categories:
            # ------------------------------------------------------------------------
            td = table.tag('tr', {'class': 'category', 'id': f'Cat_{cat}'}).tag(
                'td', {'colspan': '4'})
            td.tag('i').tag('small', text='Mod-Category')
            links = td.tag('small', text='&nbsp;&nbsp;&nbsp;&nbsp;')
            # ------------------------------------------------------------------------
            # Show navigation row for categories.
            for other_cat in all_cats:
                m = re.match('\d+_(.*)', other_cat)
                vis_other_cat = m.group(1) if m else other_cat
                links.tag('a', {'href': f'#Cat_{other_cat}',
                          'class': 'fsgreen'}, text=vis_other_cat)
                links.tag('span', text='&nbsp;&nbsp;')
            # ------------------------------------------------------------------------
            # Show category, without leading digits.
            td.tag('h1', text=f'{vis_cat}')
        # ------------------------------------------------------------------------
        # Show all mods in the current category.
        for name in sorted(mods[cat]):
            mod_list = mods[cat][name]
            for _, mod, icon, info, desc in mod_list:
                mod_number += 1
                create_mod_row(mod_number, mod, table,
                               icon, info, desc, vis_cat)
        # ------------------------------------------------------------------------
    return html


# ============================================================================
# Create the table row for the given mod.
def create_mod_row(mod_number: int, mod: Mod, table: Tag, icon: Tag, info: Tag, desc: Tag, vis_cat: str):
    tr = table.tag('tr')
    cls = {'class': 'instDiv'} if mod.is_installed else {}
    ncls = {'class': 'none' if mod.is_installed else 'fsgreen',
             'style': 'text-align:right'}
    num_td = tr.tag('td', cls)
    num_td.tag('h1', ncls, text=str(mod_number))
    
    icon_td = tr.tag('td', cls)
    icon_td.add(icon)
    icon_td.tag('div').tag('i').tag('small', {'class': 'item_cat'}, text='/'+vis_cat+'/')
    
    info_td = tr.tag('td', cls)
    info_td.add(info)
    
    tr.tag('td', {'class': 'desc'}).add(desc)


# ============================================================================
# Create a HTML representation for the mod.
def create_mod_html(mod: Mod, installed_mods: list) -> Tag:
    # ------------------------------------------------------------------------
    zipfile = mod.zipfile
    is_installed = zipfile in installed_mods
    zipfile_rel = os.path.relpath(mod.fullfile, MOD_VAULT)
    mod.is_installed = is_installed
    # ------------------------------------------------------------------------
    # A new DIV, to contain the Mod description.
    div = Tag('div', {'class': 'instDiv'} if is_installed else {})
    # ------------------------------------------------------------------------
    # Create a table (with a single row) for the Mod description.
    # 1st column: The Icon
    # 2nd column: Name, version, author, etc.
    # 3rd column: Detailed description text
    tbl = div.tag('table')
    tr = tbl.tag('tr')
    # ------------------------------------------------------------------------
    # 3 Cells for the 3 columns
    td1 = tr.tag('td')
    td2 = tr.tag('td')
    td3 = tr.tag('td', {'class': 'desc'})
    # ------------------------------------------------------------------------
    # Column 1: The image/Icon
    icon = td1.tag('img', {'src': 'data:image/png;base64,' + mod.icon_b64,
                           'width': str(IMG_SIZE), 'height': str(IMG_SIZE)})
    # ------------------------------------------------------------------------
    # Column 2: Name and information.
    info = td2.tag('div')
    info.tag('div', {'class': 'fsgreen'} if not is_installed else {}).tag(
        'b', text=f'{mod.title}')
    zip_small = info.tag('i').tag('small')
    zip_small.tag('a', {'href': zipfile_rel}, text=zipfile)

    info.tag('div', text='Version: ' + mod.version)
    info.tag('div').tag('small', text='Author: ' + mod.author)
    info.tag('div').tag('small', text='Installed:' + str(is_installed))
    info.tag('div').tag('small', text='Multiplayer:' + str(mod.multiplayer))
    search_term = mod.title.replace(' ', '+')
    modhub = 'https://farming-simulator.com/mods.php?title=fs2017&lang=en&searchMod='
    # zip_small.tag('div').tag('small').tag('a', {"target": "_blank", 'href': modhub+search_term}, text='ModHub')
    zip_small.tag('a', {'class':'fsgreen', "target": "_blank", 'href': modhub+search_term}, text='(on ModHub?)')

    # ------------------------------------------------------------------------
    # Prepare Store Item table
    num_items = len(mod.store_items)
    item_cats = {}
    for item in mod.store_items:
        cat_list = item_cats.setdefault(item.category, [])
        cat_list.append(item)
    # ------------------------------------------------------------------------
    itm_tbl = info.tag('table', {'class': 'item_list'})
    # ------------------------------------------------------------------------
    # Show number of store items in the mod.
    # itm_tbl.tag('tr', {'class': 'item_list'}).tag('td', {'colspan': '5', 'class': 'item_list'}).tag('div').tag('small', text=f'Store Items: {num_items}')
    itm_tbl.tag('tr', {'class': 'item_list'}).tag('td', {'colspan': '5', 'class': 'item_list'}).tag('div').tag('small', text=f'')
    # ------------------------------------------------------------------------
    for item_cat in sorted(item_cats):
        vis_item_cat = item_cat[:1].upper() + item_cat[1:] + ':'
        itm_tbl.tag('tr', {'class': 'item_list'}).tag('td', {'colspan': '5', 'class': 'item_list'}).tag(
            'div').tag('small', {'class': 'item_cat'}, text=f'{vis_item_cat}')
        for item in item_cats[item_cat]:
            itm_row = itm_tbl.tag('tr', {'class': 'item_list'})
            itm_row.tag('td', {'class': 'item_list'}, text='&nbsp;&nbsp;')
            itm_row.tag('td', {'class': 'item_list'}).tag(
                'small', {'class': 'brand'}, text=f'{item.brand}')
            itm_row.tag('td', {'class': 'item_list'}).tag(
                'small', {'class': 'item_name'}, text=f'&nbsp;&nbsp;{item.name}')
            item_price = int(item.price)
            itm_row.tag('td', {'class': 'item_list', 'style': 'text-align:right'}).tag(
                'small', {'class': 'item_price'}, text=f'&nbsp;&nbsp;<code>$&nbsp;{item_price:,}</code>')
            itm_row.tag('td', {'class': 'item_list', 'style': 'text-align:right'}).tag(
                'small', {'class': 'item_upkeep'}, text=f'&nbsp;&nbsp;<code>(${item.dailyUpkeep}/d)</code>')
    # ------------------------------------------------------------------------
    # Column 3: Detailed Mod description
    desc = td3.tag('small', text=mod.description)
    # ------------------------------------------------------------------------
    return div, mod, icon, info, desc


# ============================================================================
# Get a list of zip files in the given folder.
def get_zipfiles(folder: str) -> list:
    # ------------------------------------------------------------------------
    # Convert "~" into the users home folder.
    folder = os.path.expanduser(folder)
    zipfiles = []
    # ------------------------------------------------------------------------
    # Get all zip files in folder.
    for root, _, files in os.walk(folder):
        zipfiles += [os.path.join(root, filename)
                     for filename in files if filename.endswith('.zip')]
    # ------------------------------------------------------------------------
    return zipfiles


# ============================================================================
if __name__ == '__main__':
    main()


# ============================================================================
# End of file.
# ============================================================================
