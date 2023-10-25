#%%
import requests
from bs4 import BeautifulSoup

#%%
# ChordSheet object will take url and format the chords in two ways: self.chords with [ch](*.?)[/ch] tags and self.fmt_chords as formatted but uneditable chords
# Pass use_sharps variable for properly writing chords to prefer flats or sharps
# May not be robust with accidentals
class ChordSheet:
    
    def __init__(self,url,use_sharps,from_file=False):
        self.use_sharps = use_sharps # setting member variable to whether using sharps or flats, sharps as True
        self.sharps = "A,A#,B,C,C#,D,D#,E,F,F#,G,G#".split(",") # string to list variable, index based keys in sharps
        self.flats = "A,Bb,B,C,Db,D,Eb,E,F,Gb,G,Ab".split(",") # corresponds to same as above index for flats
        self.num_keys = 12 # number of key indexes, does not change
        if from_file:
            self.chords = from_file
        else:
            soup = self.load_song_link(url)
            chords = self.get_chords(soup)
            self.chords = self.transpose_all(chords,0) # chords with markers
        self.fmt_chords = self.format_chords(self.chords) # chords pretty format
        
    # Scrape webpage for link, may require time.sleep at the end if network is slow
    # Pass in ultimate-guitar.com chord sheet URL
    def load_song_link(self,url):
        
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.text,'html.parser')
        
        return soup
    
    # Scraping raw text from page, splitting at markers to cut out useless garbage data from UG
    # Pass in BeautifulSoup object
    def get_chords(self,soup):
        
        prettytext = soup.prettify()
        
        try:
            prettytext = prettytext.split('"tab_view":{"wiki_tab":{"content":"')[1].split('","revision_id"')[0] # weird string marker to find the starting point
        except:
            try:
                prettytext = prettytext.split('{&quot;content&quot;:&quot;')[1].split('&quot;,&quot;revision_id&quot;')[0]
            except:
                return None
        # some pages have a different string marker, may need to create more exceptions if neither work for a given chord page    
        return prettytext
    
    # Transpose chord based on direction and accidental type
    # Pass in direction (+/-1 chromatic step or 0 if only changing accidental type), bool variable to know if the chord being changed is sharp or flat
    def transpose_chord(self,chord,direction,contains_sharps):
        
        if self.use_sharps: # check if intended accidental is sharp
            if not contains_sharps: # if the chord being changed is not sharp
                chord_index = self.flats.index(chord) + direction # finding the chord index using the flats list
                return self.sharps[chord_index%self.num_keys] # using chord index with sharps list
            else:
                chord_index = self.sharps.index(chord) + direction # finding the chord index using the sharps list
                return self.sharps[chord_index%self.num_keys] # using chord index with sharps list
        else:
            if contains_sharps:
                chord_index = self.sharps.index(chord) + direction # finding the chord index using the sharps list
                return self.flats[chord_index%self.num_keys] # using chord index with flats list
            else:
                chord_index = self.flats.index(chord) + direction # finding the chord index using the flats list
                return self.flats[chord_index%self.num_keys] # using chord index with flats list
        
    def transpose_all(self,chords,direction):
        
        chords = chords.split(r'[ch]') # splitting the chords list to the start of each chord (i.e. "Abdim7/B[/ch]..." can be one item in the list)
        
        for i in range(len(chords)):
            if r'[/ch]' in chords[i]: # make sure item in chords list is an actual chord
                long_replace = False # long replace refers to chords of more than one char (i.e. "Ab"), default to False
                if chords[i][1] == 'b': # chord contains flat, requiring long_replace = True
                    long_replace = True
                    newchord = self.transpose_chord(chords[i][0:2],direction,contains_sharps=False) # transpose chord including accidental
                elif chords[i][1] == '#': # same as above for sharp
                    long_replace = True
                    newchord = self.transpose_chord(chords[i][0:2],direction,contains_sharps=True) # transpose chord including accidental
                else:
                    newchord = self.transpose_chord(chords[i][0],direction,contains_sharps=self.use_sharps) # one char chord transposition
                    
                if long_replace:
                    chords[i] = newchord + chords[i][2:] # replacing two char chord
                else:
                    chords[i] = newchord + chords[i][1:] # replacing one char chord
                    
                if r"/" in chords[i].split(r'[/ch]')[0]: # case for secondary key (i.e. C/E requires a second transposition)
                    long_replace = False
                    sub = chords[i].split(r'/')[1] # string for secondary chord repeating all above transposition steps
                    if sub[1] == "b":
                        long_replace = True
                        newchord = self.transpose_chord(sub[0:2],direction,contains_sharps=False)
                    elif sub[1] == "#":
                        long_replace = True
                        newchord = self.transpose_chord(sub[0:2],direction,contains_sharps=True)
                    else:
                        newchord = self.transpose_chord(sub[0],direction,contains_sharps=self.use_sharps)
                        
                    if long_replace:
                        sub = newchord + sub[2:]
                    else:
                        sub = newchord + sub[1:]
                    sub = r"".join(sub[:-1]) # put sub back together as string to append into chords variable
                    chords[i] = chords[i].split(r'[/ch]')[0].split(r'/')[0] + r'/' + sub + r'[/ch]' + chords[i].split(r'[/ch]')[1] # appending sub variable into chord item
    
        return '[ch]'.join(chords) # rejoining the chords list with [ch](*.?)[/ch] format
    
    # Removes tags from chords_text string to print text in readable format
    # Returns a list variable where each index is made for a new line
    def format_chords(self,chords_text):
        
        chords_text = chords_text.replace("[ch]","").replace(r"[/ch]","").replace("[tab]","").replace("[/tab]","")
        chords_text = chords_text.split(r'\r\n')
        
        return chords_text
    
    # Change chords and fmt_chords member variables to sharps
    def sharpen(self):
        self.use_sharps = True
        self.chords = self.transpose_all(self.chords,0)
        self.fmt_chords = self.format_chords(self.chords)

    # Change chords and fmt_chords member variables to flats
    def flatten(self):
        self.use_sharps = False
        self.chords = self.transpose_all(self.chords,0)
        self.fmt_chords = self.format_chords(self.chords)
        
    def up(self):
        self.chords = self.transpose_all(self.chords,1)
        self.fmt_chords = self.format_chords(self.chords)
        
    def down(self):
        self.chords = self.transpose_all(self.chords,-1)
        self.fmt_chords = self.format_chords(self.chords)
        
#%%
import sys

# to prevent the "QWidget: Must construct a QApplication before a QWidget" error, you should put the code below
from PyQt5.QtCore import Qt

from PyQt5 import QtWidgets
from PyQt5.QtGui import QFont

from fpdf import FPDF

class HelpWindow(QtWidgets.QWidget):
    
    def __init__(self):
        
        QtWidgets.QWidget.__init__(self)
        
        self.layout = QtWidgets.QVBoxLayout()
        self.setGeometry(500,400,400,200)
        self.setWindowTitle('About')
        
        self.helptext = QtWidgets.QPlainTextEdit()

        self.helptext.setPlainText("For We The Redeemed Praise/Ops use only.\nPlease email <hongjere560@gmail.com> with any questions.")
        self.helptext.setReadOnly(True)
        self.layout.addWidget(self.helptext)
        
        self.setLayout(self.layout)

class MetaDataWindow(QtWidgets.QWidget):
    
    def __init__(self,metadata):
        
        QtWidgets.QWidget.__init__(self)
        
        self.metadata = metadata
        
        self.layout = QtWidgets.QVBoxLayout()
        self.setGeometry(1200,600,800,640)
        self.setWindowTitle('Metadata')
        
        self.song_label = QtWidgets.QLabel()
        self.song_label.setText("Song Title:")
        self.layout.addWidget(self.song_label)
        
        self.song_entry = QtWidgets.QLineEdit()
        self.layout.addWidget(self.song_entry)
        
        self.artist_label = QtWidgets.QLabel()
        self.artist_label.setText("Artist Name:")
        self.layout.addWidget(self.artist_label)
        
        self.artist_entry = QtWidgets.QLineEdit()
        self.layout.addWidget(self.artist_entry)
        
        self.key_label = QtWidgets.QLabel()
        self.key_label.setText("Song Key:")
        self.layout.addWidget(self.key_label)
        
        self.key_entry = QtWidgets.QLineEdit()
        self.layout.addWidget(self.key_entry)
        
        self.description_label = QtWidgets.QLabel()
        self.description_label.setText("Description:")
        self.layout.addWidget(self.description_label)
        
        self.description_field = QtWidgets.QTextEdit()
        self.layout.addWidget(self.description_field)
        
        self.notes_label = QtWidgets.QLabel()
        self.notes_label.setText("Notes:")
        self.layout.addWidget(self.notes_label)
        
        self.notes_field = QtWidgets.QTextEdit()
        self.layout.addWidget(self.notes_field)
        
        self.btnUpdate = QtWidgets.QPushButton()
        self.btnUpdate.setText("Update")
        self.layout.addWidget(self.btnUpdate)
        self.btnUpdate.clicked.connect(self.update)
        
        self.populateMetadata(self.metadata)
        self.setWindowModality(Qt.ApplicationModal)

        self.setLayout(self.layout)
        
    def populateMetadata(self,metadata):
        
        self.song_entry.setText(metadata[0])
        self.artist_entry.setText(metadata[1])
        self.key_entry.setText(metadata[2])
        self.description_field.setText(metadata[3])
        self.notes_field.setText(metadata[4])
    
    def update(self):
        
        self.metadata[0] = self.song_entry.text()
        self.metadata[1] = self.artist_entry.text()
        self.metadata[2] = self.key_entry.text()
        self.metadata[3] = self.description_field.toPlainText()
        self.metadata[4] = self.notes_field.toPlainText()
        
        self.populateMetadata(self.metadata)
        self.close()
    
class Window(QtWidgets.QWidget):
    
    def __init__(self):
        
        super().__init__()
        self.setWindowTitle('UG Chord Parser')
        self.setGeometry(1000,500,800,640)
                
        self.use_sharps = True
        
        self.font = 'Courier'
        self.font_size = 10
        
        self.metadata = ["","","","",""] # Index 0: Song Title, 1: Artist, 2: Key, 3: Description, 4: Notes
        
        self.UG = 0 # Initialize UG variable as 0, when given URL this variable is set to ChordSheet object

        self.lay = QtWidgets.QGridLayout()

        self.songlink = QtWidgets.QLineEdit()
        self.lay.addWidget(self.songlink,0,0,1,5)
        
        self.btnLoadURL = QtWidgets.QPushButton()
        self.btnLoadURL.setText("Load Song")
        self.btnLoadURL.setMaximumWidth(100)
        self.lay.addWidget(self.btnLoadURL,0,5,1,1)
        self.btnLoadURL.clicked.connect(self.loadURL)

        self.radiobutton1 = QtWidgets.QRadioButton("Sharps (#)")
        self.radiobutton1.setChecked(True)
        self.radiobutton1.clicked.connect(lambda: self.checkAccidental())
        self.lay.addWidget(self.radiobutton1,1,0)
        self.radiobutton2 = QtWidgets.QRadioButton("Flats (b)")
        self.radiobutton2.clicked.connect(lambda: self.checkAccidental())
        self.lay.addWidget(self.radiobutton2,1,1)
        
        self.btnUp = QtWidgets.QPushButton()
        self.btnUp.setText('+')
        self.lay.addWidget(self.btnUp,2,0)
        self.btnUp.clicked.connect(self.raiseKey)
        
        self.btnDown = QtWidgets.QPushButton()
        self.btnDown.setText('-')
        self.lay.addWidget(self.btnDown,2,1)
        self.btnDown.clicked.connect(self.lowerKey)
        
        self.chordbox = QtWidgets.QTextEdit()
        self.chordbox.setFont(QFont(self.font,self.font_size))
        self.chordbox.resize(400,800)
        self.lay.addWidget(self.chordbox,3,0,8,8)
        
        self.btnExportPDF = QtWidgets.QPushButton()
        self.btnExportPDF.setText('Export To PDF')
        self.lay.addWidget(self.btnExportPDF,11,7,1,1)
        self.btnExportPDF.clicked.connect(self.exportToPDF)
        
        self.main_menu = QtWidgets.QMenuBar()
        self.file_menu = self.main_menu.addMenu("File")
        self.edit_menu = self.main_menu.addMenu("Options")
        self.help_menu = self.main_menu.addMenu("Help")

        self.open_action = QtWidgets.QAction("Open song file",self)
        self.open_action.triggered.connect(self.openSong)
        self.save_action = QtWidgets.QAction("Save song file",self)
        self.save_action.triggered.connect(self.saveSong)
        self.file_menu.addAction(self.open_action)
        self.file_menu.addAction(self.save_action)
        
        self.edit_meta = QtWidgets.QAction("Edit Metadata",self)
        self.edit_meta.triggered.connect(self.editMeta)
        self.edit_menu.addAction(self.edit_meta)
        
        self.edit_font = QtWidgets.QAction("Show font",self)
        self.edit_font.triggered.connect(self.editFont)
        self.edit_menu.addAction(self.edit_font)
        
        self.how_to_use = QtWidgets.QAction("About",self)
        self.how_to_use.triggered.connect(self.readMe)
        self.help_menu.addAction(self.how_to_use)
        
        self.lay.setMenuBar(self.main_menu)

        self.setLayout(self.lay)

    def checkAccidental(self):
        
        if '#' in self.sender().text():
            self.use_sharps = True
        else:
            self.use_sharps = False

        if self.UG != 0:
            if self.use_sharps:
                self.UG.sharpen()
            else:
                self.UG.flatten()
            self.updateChords()
            
    def saveSong(self):
        
        if self.UG != 0:
            filename = QtWidgets.QFileDialog.getSaveFileName(self, 'Save file',filter="Song files (*.wtr)")
            if filename[0]:
                with open(filename[0],'w+',encoding="utf-8") as f:
                    f.write("{$meta}".join(self.metadata) + '\n')
                    f.write(self.UG.chords)
        else:
            self.chordbox.setText("No song data to save")

    def openSong(self):
        
        filename = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file',filter="Song files (*.wtr)")
        if filename[0]:
            with open(filename[0],'r',encoding="utf-8") as f:
                lines = f.readlines()
            self.metadata = lines[0].split("{$meta}")
            self.UG = ChordSheet("", self.use_sharps, from_file=lines[1])
            self.updateChords()
    
    def editMeta(self):
        
        if self.UG != 0:
            self.meta_window = MetaDataWindow(self.metadata)
            self.meta_window.show()
            self.metadata = self.meta_window.metadata
        else:
            self.chordbox.setText("No song data to write in metadata")
        
    def editFont(self):
        
        self.about_window = HelpWindow()
        self.about_window.helptext.setPlainText("Font: %s\nFont Size: %d"%(self.font,self.font_size))
        self.about_window.setWindowTitle("Font Info")
        self.about_window.show()
        
    def readMe(self):
        
        self.help_window = HelpWindow()
        self.help_window.show()
    
    def loadURL(self):
        
        url = self.songlink.text()
        if ("ultimate-guitar.com" in url) and ("chords" in url):
            self.metadata = ["","","","",""]
            try:
                self.UG = ChordSheet(url, self.use_sharps)
                self.updateChords()
            except:
                self.UG = 0
                self.chordbox.setText("Parse error")
        else:
            self.UG = 0
            self.chordbox.setText("Unknown link encountered")
    
    def updateChords(self):
        
        self.chordbox.setText("\n".join(self.UG.fmt_chords))
    
    def raiseKey(self):
        
        if self.UG != 0:
            self.UG.up()
            self.updateChords()
    
    def lowerKey(self):
        
        if self.UG != 0:
            self.UG.down()
            self.updateChords()
    
    def exportToPDF(self):
        
        if self.UG != 0:
            filename = QtWidgets.QFileDialog.getSaveFileName(self, 'Export PDF',filter="PDF Document (*.pdf)")
            if filename[0]:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font(self.font,size = self.font_size)
                lines = self.chordbox.toPlainText().encode('latin-1', 'replace').decode('latin-1').split('\n')
                for line in lines:
                    pdf.cell(200,5,txt=line,ln=1,align='L')
                pdf.output(filename[0])
        else:
            self.chordbox.setText("No song data to export")

if __name__ == "__main__":
    
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())