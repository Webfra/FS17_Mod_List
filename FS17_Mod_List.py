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
        div = create_mod_html(mod, installed_mods)
        # ------------------------------------------------------------------------
        mods['maps' if mod.has_maps else 'other'].append(div)

    # ------------------------------------------------------------------------
    doc = create_html_doc(mods)

    # ------------------------------------------------------------------------
    out_file = os.path.abspath(os.path.join(MOD_VAULT, OUTPUT_FILE))
    print(f'Writing HTML file: {out_file} ...')
    doc.save(out_file)
    # ------------------------------------------------------------------------


# ============================================================================
# Create a HTML document from the mods dictionary.
def create_html_doc(mods: dict) -> Html:
    # ------------------------------------------------------------------------
    # Start a new HTML file.
    html = Html()
    # ------------------------------------------------------------------------
    # Create a <head> tag.
    html.head.tag('title', text=HTML_TITLE)
    with open('styles.css', 'rt') as css:
        html.head.tag('style', {'type': 'text/css'}, text=css.read())
    # ------------------------------------------------------------------------
    # Create a <body> tag.
    body = html.body
    body.tag('h1', {'class': 'fsgreen'}, text=HTML_TITLE)
    # ------------------------------------------------------------------------
    # Add all "other" mods.
    body.tag('h1', text='Category: Other Mods')
    for div in mods['other']:
        body.tag('hr')
        body.add(div)
    # ------------------------------------------------------------------------
    # Add all "map" mods.
    body.tag('hr')
    body.tag('h1', text='Category: Maps')
    for div in mods['maps']:
        body.tag('hr')
        body.add(div)
    # ------------------------------------------------------------------------
    return html


# ============================================================================
# Create a HTML representation for the mod.
def create_mod_html(mod: Mod, installed_mods: list) -> Tag:
    # ------------------------------------------------------------------------
    zipfile = os.path.basename(mod.zipfile)
    is_installed = zipfile in installed_mods
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
    td1.tag('img', {'src': 'data:image/png;base64,' + mod.icon_b64,
            'width': str(IMG_SIZE), 'height': str(IMG_SIZE)})
    # ------------------------------------------------------------------------
    # Column 2: Name and information.
    td2.tag('div', {'class': 'fsgreen'} if not is_installed else {}).tag(
        'b', text=f'{mod.title}')
    td2.tag('i').tag('small').tag('a', {'href': zipfile}, text=zipfile)
    td2.tag('div', text='Version: ' + mod.version)
    td2.tag('div').tag('small', text='Author: ' + mod.author)
    td2.tag('div').tag('small', text='Installed:' + str(is_installed))
    td2.tag('div').tag('small', text='Multiplayer:' + str(mod.multiplayer))
    # ------------------------------------------------------------------------
    # Column 3: Detailed Mod description
    td3.tag('small', text=mod.description)
    # ------------------------------------------------------------------------
    return div


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
