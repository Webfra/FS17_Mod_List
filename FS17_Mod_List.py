import os
import sys

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

    # ------------------------------------------------------------------------
    # Get the list of Mods in the current folder.
    print('Finding Mods in', os.path.abspath(MOD_VAULT))
    list_of_zipfiles = get_zipfiles(MOD_VAULT)
    if len(list_of_zipfiles) <= 0:
        print('***ERROR: No Mods (ZIP files) found in:',
              os.path.abspath(MOD_VAULT))
        sys.exit(-1)

    # ------------------------------------------------------------------------
    mods = {'maps': [], 'other': []}

    # ------------------------------------------------------------------------
    # Read MOD information and prepare HTML content.
    num_mods = len(list_of_zipfiles)
    print(f'Reading information for {num_mods} mods...')
    for _, zipfile in enumerate(list_of_zipfiles):
        # ------------------------------------------------------------------------
        # Show progress.
        # print(idx+1, 'of', len(list_of_zipfiles), zipfile)
        zipfile_vault = os.path.join(MOD_VAULT, zipfile)
        # ------------------------------------------------------------------------
        # Collect information about the mod.
        mod = Mod(zipfile_vault, GAME_DIR, IMG_SIZE)
        # ------------------------------------------------------------------------
        # Create a HTML representation for the mod.
        div, mod, icon, info, desc = create_mod_html(mod, installed_mods)
        # ------------------------------------------------------------------------
        mods['maps' if mod.has_maps else 'other'].append( (div, mod, icon, info, desc) )

    # ------------------------------------------------------------------------
    doc = create_html_doc(mods)

    # ------------------------------------------------------------------------
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
    mod_number = 0
    # Create a <body> tag.
    body = html.body
    body.tag('h1', {'class': 'fsgreen'}, text=HTML_TITLE)
    table = body.tag('table')

    # ------------------------------------------------------------------------
    # Add all "other" mods.
    table.tag('tr').tag('td', { 'colspan':'4'}).tag('h2', text='Category: Other Mods')
    for _, mod, icon, info, desc in mods['other']:
        mod_number += 1
        create_mod_row(mod_number, mod, table, icon, info, desc)

    # ------------------------------------------------------------------------
    # Add all "map" mods.
    # body.tag('hr')
    table.tag('tr').tag('td', { 'colspan':'4'}).tag('h2', text='Category: Maps')
    for _, mod, icon, info, desc in mods['maps']:
        mod_number += 1
        create_mod_row(mod_number, mod, table, icon, info, desc)
    # ------------------------------------------------------------------------
    return html


# ============================================================================
def create_mod_row(mod_number:int, mod: Mod, table:Tag, icon:Tag, info:Tag, desc:Tag):
    tr = table.tag('tr')
    tr.tag('td', {'class': 'instDiv'} if mod.is_installed else {}).tag('h1', {'class': 'none' if mod.is_installed else 'fsgreen', 'style':'text-align:right'}, text=str(mod_number))
    tr.tag('td', {'class': 'instDiv'} if mod.is_installed else {}).add(icon)
    tr.tag('td', {'class': 'instDiv'} if mod.is_installed else {}).add(info)
    tr.tag('td', {'class': 'desc'}).add(desc)


# ============================================================================
# Create a HTML representation for the mod.
def create_mod_html(mod: Mod, installed_mods: list) -> Tag:
    # ------------------------------------------------------------------------
    zipfile = os.path.basename(mod.zipfile)
    is_installed = zipfile in installed_mods
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
    info.tag('i').tag('small').tag('a', {'href': zipfile}, text=zipfile)
    info.tag('div', text='Version: ' + mod.version)
    info.tag('div').tag('small', text='Author: ' + mod.author)
    info.tag('div').tag('small', text='Installed:' + str(is_installed))
    info.tag('div').tag('small', text='Multiplayer:' + str(mod.multiplayer))
    search_term = mod.title.replace(' ', '+')
    modhub = 'https://farming-simulator.com/mods.php?title=fs2017&lang=en&searchMod='
    info.tag('div').tag('small').tag('a', {"target": "_blank",
                                          'href': modhub+search_term}, text='ModHub')
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
    # ------------------------------------------------------------------------
    # Get all zip files in folder.
    for _, _, files in os.walk(folder):
        return [filename for filename in files if filename.endswith('.zip')]


# ============================================================================
if __name__ == '__main__':
    main()


# ============================================================================
# End of file.
# ============================================================================
