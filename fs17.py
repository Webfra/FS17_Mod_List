""" Module to provide Farming Simulator 17 related functions and classes.
"""

import xml.etree.ElementTree as ET

import os
import re
from zipfile import ZipFile
from io import BytesIO
import base64


# Pillow Image library (pip install pillow)
from PIL import Image


# ============================================================================
class Mod(object):
    """ Represents a FS17 Mod.

    Mods (in Zip files) can be read and some information will be available
    via its member variables.
    """
    # ========================================================================
    def __init__(self, zipfile: str, GAME_DIR: str, IMG_SIZE: int) -> None:
        # ------------------------------------------------------------------------
        self.GAME_DIR: str = GAME_DIR
        '''The installation folder of the FS17 game.'''
        self.IMG_SIZE: int = IMG_SIZE
        '''The size, to which all icons will be scaled to.'''
        # ------------------------------------------------------------------------
        self.zipfile = os.path.basename(zipfile)
        self.fullfile = zipfile
        '''The name of the ZIP file of the Mod.'''
        self.modDesc = ET.Element('')
        '''The modDesc.xml as xml.etree.ElementTree Element'''
        self.has_maps = False
        '''True, if the Mod contains a map.'''
        self.title = ''
        '''The title of the Mod'''
        self.icon_b64 = ''
        '''Base64 representation of the Mod icon.'''
        self.author = ''
        '''Author of the Mod.'''
        self.version = ''
        '''Version of the Mod.'''
        self.description = ''
        '''Mod description, can be lenghty...'''
        self.multiplayer = False
        '''True, if the Mod claims to support multiplayer.'''
        # ------------------------------------------------------------------------
        self.load()

    # ========================================================================
    def load(self) -> None:
        # ------------------------------------------------------------------------
        with ZipFile(self.fullfile, 'r') as zip:
            # ------------------------------------------------------------------------
            self.ZipFile = zip
            # ------------------------------------------------------------------------
            # Read the modDesc.xml file content.
            xml = zip.read('modDesc.xml').decode()
            # ------------------------------------------------------------------------
            # Fix a few issues with the modDesc.xml of some mods.
            # Otherwise, ET.fromstring() will fail!
            xml = Mod._fix_xml(xml)
            # ------------------------------------------------------------------------
            # Create an ET Element from the XML.
            self.modDesc = ET.fromstring(xml)
            # ------------------------------------------------------------------------
            # Is the mod a Map?
            self.has_maps = self.modDesc.find('./maps') is not None
            # ------------------------------------------------------------------------
            # Get the Mod title.
            self.title = self._get_mod_title()
            # ------------------------------------------------------------------------
            # Get the Base64 representation of the icon from the ZIP file.
            self.icon_b64 = self._find_icon(zip)
            # ------------------------------------------------------------------------
            # Get Author name and version
            self.author = self.modDesc.find('./author').text
            self.version = self.modDesc.find('./version').text
            # ------------------------------------------------------------------------
            # Get the description text of the Mod
            description = self.modDesc.find('./description')
            description_en = description.find('./en')
            if description_en is not None:
                description = description_en
            self.description = description.text.strip().replace('\n', '<br>\n')
            # ------------------------------------------------------------------------
            # Is Multiplayer supported?
            self.multiplayer = False
            MP = self.modDesc.find('./multiplayer')
            if MP is not None:
                if 'supported' in MP.attrib:
                    self.multiplayer = MP.attrib['supported'] == 'true'
            # ------------------------------------------------------------------------
            # Get the listed store items.
            self.store_item_xmls = [item.attrib['xmlFilename'] for item in self.modDesc.findall('./storeItems/storeItem')]
            # self.store_items = [ Item(ET.fromstring(zip.read(item_xml).decode())) for item_xml in self.store_item_xmls ]
            self.store_items = []
            for item_xml in self.store_item_xmls:
                print(' -- ', item_xml)
                try:
                    xml = zip.read(item_xml)
                except:
                    print(f'***WARNING: Error reading store item file: {item_xml} from zip file: {self.fullfile}' )
                    continue
                try:
                    xml = xml.decode() 
                except:
                    print(f'***WARNING: Invalid store item file: {item_xml} from zip file: {self.fullfile}' )
                    continue
                try:
                    xml = Mod._fix_xml(xml)
                    xml = ET.fromstring(xml)
                except Exception as e:
                    print(f'***WARNING: Invalid XML file: {item_xml} from zip file: {self.fullfile}' )
                    print(e)
                    continue
                self.store_items.append(Item(self, xml))
            # ------------------------------------------------------------------------
            del self.ZipFile

    # ============================================================================
    # Fix a few issues with the modDesc.xml of some mods.
    # Otherwise, ET.fromstring() will fail!
    @staticmethod
    def _fix_xml(xml: str) -> str:
        # ------------------------------------------------------------------------
        # Ampersand is not allowed raw!
        xml = xml.replace(' & ', ' and ')
        # -- is not allowed raw!
        xml = xml.replace('Fill--and', 'Fill-and')
        # Some spaces are missing in some files.
        xml = xml.replace('partOfEconomy="true"', 'partOfEconomy="true" ')
        xml = xml.replace('"configFilename=', '" configFilename=')
        xml = xml.replace('"baleTypesDirectory=', '" baleTypesDirectory=')
        # Some more invalid tokens in Beta mods.
        xml = xml.replace('Bressel&Lade', 'Bressel+Lade')
        xml = xml.replace('and enjoy.]]></de>', 'and enjoy.</de>')

        xml = xml.replace('"endTransLimit="', '" endTransLimit="')
        xml = xml.replace('"translationActive="', '" translationActive="')
        xml = xml.replace('"scaleActive="', '" scaleActive="')
        xml = xml.replace('"playSound="', '" playSound="')
        xml = xml.replace('"rotationActive="', '" rotationActive="')
        xml = xml.replace('"visibilityActive="', '" visibilityActive="')
        xml = xml.replace('"index="', '" index="')


        xml = xml.replace('<function>https://www.facebook.com/ETA-La-Marchoise-318371215013344/?ref=ts&fref=ts</function>', '')

        xml = xml.replace('-- aanimazioni tubi --', ' aanimazioni tubi ')

        # Remove comments

        # Comment-shenanigans in FS17_Guellepack.zip
        xml = re.sub(r'^<!--<vehicleTypeConfigurations>(.*?)^-->\s*$', '\n\n\n\n\n\n\n\n\n', xml, flags=re.MULTILINE | re.DOTALL)

        xml = re.sub(r'<!--(.*?)-->', '<!-- -->', xml )
        
        # ------------------------------------------------------------------------
        return xml

    # ============================================================================
    # Find the icon
    def _find_icon(self, zip: ZipFile) -> str:
        # ------------------------------------------------------------------------
        # Get the icon file name.
        icon_file = self.modDesc.find('./iconFilename')
        # Check, if there is a sub-tag "<en>".
        icon_file_en = icon_file.find('./en')
        if icon_file_en is not None:
            icon_file = icon_file_en
        # Get the text of the tag.
        icon_file = icon_file.text
        # Store original name of the icon file, for reporting.
        icon_file_org = icon_file
        # ------------------------------------------------------------------------
        # Is the file referring to the Game's store?
        data_store = os.path.join(self.GAME_DIR, 'data', 'store')
        icon_file = icon_file.replace('$data/store/', data_store+'/')
        # ------------------------------------------------------------------------
        while True:
            # ------------------------------------------------------------------------
            try:
                icon_b64 = Mod.get_icon(zip, icon_file, self.IMG_SIZE)
            # ------------------------------------------------------------------------
            except KeyError:
                # ------------------------------------------------------------------------
                # Some mods have the wrong file extension (.png instead of .dds), fix it and try again.
                if icon_file.endswith('.png'):
                    icon_file = icon_file.replace('.png', '.dds')
                    continue
                # ------------------------------------------------------------------------
                # FATAL: Unable to find icon file.
                print('Unkown Icon file:', icon_file_org, " in ", self.zipfile)
                raise KeyError
            break
        # ------------------------------------------------------------------------
        return icon_b64

    # ============================================================================
    @staticmethod
    def get_icon(zip: ZipFile, icon_name: str, IMG_SIZE: int) -> str:
        # ------------------------------------------------------------------------
        # Try to read the icon from the zip file.
        try:
            in_bytes = zip.read(icon_name)
        # ------------------------------------------------------------------------
        # Otherwise, try to read the file from local storage
        except:
            # Check if the file exists outside the ZIP file.
            if os.path.exists(icon_name):
                with open(icon_name, 'rb') as f_in:
                    in_bytes = f_in.read()
            else:
                raise KeyError
        # ------------------------------------------------------------------------
        # Read the icon image and convert it to a Base64 representation PNG.
        with BytesIO(in_bytes) as in_stream:
            # Open the image using PIL Image.
            image = Image.open(in_stream)
            # Scale the image to standard size.
            image = image.resize((IMG_SIZE, IMG_SIZE))
            # Convert the image.
            with BytesIO() as out_stream:
                # Convert Image to PNG.
                image.save(out_stream, format='png')
                # Convert Image to Base64.
                out_base64 = base64.b64encode(out_stream.getvalue()).decode()
        # ------------------------------------------------------------------------
        return out_base64

    # ============================================================================
    # Get the title of the mod from the mod description XML.
    def _get_mod_title(self) -> str:
        title = self.l10n(self.modDesc.find('./title'))
        if title == '':
            return 'UNKNOWN'
        return title

    # ============================================================================
    def l10n(self, node) -> str:
        sub = None
        if node is not None:
            sub = node.find('./en')
            if sub is None:
                sub = node.find('./de')
                if sub is None:
                    sub = node.find('./fr')
        result = ''
        if node is not None:
            result = node.text
        if sub is not None:
            result = sub.text
        if result.startswith('$l10n_'):
            result = self._l10n(result)
        return result

    # ============================================================================
    def _l10n(self, text:str) -> str:
        to_find = text.replace('$l10n_','')
        l10ns = self.modDesc.findall('./l10n/text')
        for l10n in l10ns:
            if l10n.attrib['name'] == to_find:
                return self.l10n(l10n)
        l10n = self.modDesc.find('./l10n')
        if l10n is not None:
            if 'filenamePrefix' in l10n.attrib:
                prefix = l10n.attrib['filenamePrefix']
                # ------------------------------------------------------------------------
                # Read the modDesc.xml file content.
                xml = self.ZipFile.read(prefix+'_en.xml').decode()
                xml = ET.fromstring(xml)
                l10n_texts = xml.findall('./texts/text')
                for l10n_text in l10n_texts:
                    if l10n_text.attrib['name'] == to_find:
                        return l10n_text.attrib['text']
                # ------------------------------------------------------------------------
        return text


# ============================================================================
class Item(object):
    # ============================================================================
    def __init__(self, mod:Mod, xml:ET.Element) -> None:
        self.xml = xml
        self.category = mod.l10n(xml.find('./storeData/category'))
        try:
            self.brand = mod.l10n(xml.find('./storeData/brand'))
        except AttributeError as e:
            self.brand = ''  # '(no brand)'

        self.name = mod.l10n(xml.find('./storeData/name'))

        self.price = '0'
        self.dailyUpkeep = '0'
        
        try:
            self.price = xml.find('./storeData/price').text
        except AttributeError as e:
            self.price = '0'

        try:
            self.dailyUpkeep = xml.find('./storeData/dailyUpkeep').text
        except AttributeError as e:
            self.dailyUpkeep = '0'

    # ============================================================================
    


# ============================================================================
# End of file.
# ============================================================================
