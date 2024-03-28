import os
import fitz
# from tqdm import tqdm
from googletrans import Translator

# from lemminflect import getLemma
# from textblob import Word
# from stanfordcorenlp import StanfordCoreNLP
# import json
# from nltk import download

# from nltk.stem import WordNetLemmatizer
# from nltk.tokenize import RegexpTokenizer
# from nltk.stem.snowball import SnowballStemmer

from PyQt6.QtWidgets import (QMainWindow, QApplication,QFileDialog , QPushButton, QComboBox , QWidget, QFormLayout,
QProgressBar,QMessageBox,QDialogButtonBox,QCheckBox,QLineEdit)
from PyQt6.QtWidgets import QLabel 
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtCore import Qt
import sys
import re



def find_highlighted_words(file_path , prog_bar):
    doc = fitz.open(file_path)
    highlight_text = []
    
    prog_bar.setRange(0, len(doc) )
    
    
    for page in doc:
        prog_bar.setValue( prog_bar.value()+1 )
        page_highlights = []
        try:
            annot = next(page.annots()) # page.firstAnnot
        except: 
            annot = False
        
        while annot:
            if annot.type[0] == 8:
                all_coordinates = annot.vertices
                if len(all_coordinates) == 4:
                    highlight_coord = fitz.Quad(all_coordinates).rect
                    highlight_coord[1] +=0.5
                    highlight_coord[3] -=4
                    
                    highlight_coord[0] +=1.5
                    highlight_coord[2] -=1.5
                    page_highlights.append(highlight_coord)
                else:
                    all_coordinates = [all_coordinates[x:x+4] for x in range(0, len(all_coordinates), 4)]
                    for i in range(0,len(all_coordinates)):
                        coord = fitz.Quad(all_coordinates[i]).rect
                        page_highlights.append(coord)

            annot = annot.next
            
        page_words = page.get_text_words()
            
        for h in page_highlights:
            sentence = [w[4] for w in page_words if   fitz.Rect(w[0:4]).intersects(h)]
            highlight_text.append(" ".join(sentence))
        # print(page_highlights)
        
    return highlight_text,len(doc)

def Translate_and_Write_file(highlighted_words ,target_file_name='FlashCards.txt' , dest_lang='fa' , prog_bar=None , deck_name=None,tags=None):
    translator = Translator()
    
    
    with open( target_file_name, "w", encoding="utf-8") as file1:
        file1.writelines('#separator:tab\n')
        file1.writelines('#html:true\n') 
        file1.writelines('#notetype:Basic\n')
        if deck_name != None: file1.writelines('#deck column:3\n')
        if tags != None: file1.writelines('#tags column:4\n')
        
        for word in highlighted_words:
            # lemma_word = lemma(word)
            # from nltk.stem import WordNetLemmatizer
            # lemmatizer = WordNetLemmatizer()
            # print(lemmatizer.lemmatize(word))
            lemma_word = re.sub("[!@#$,.%&=+/()]", '', word)
            # lemma_word = Word(word).lemmatize()

            translation_target = translator.translate(  lemma_word  , dest=dest_lang )
            translation_eng = translator.translate(  lemma_word , dest='en')

            prononc = translation_eng.extra_data['translation'][-1][-1]
            if type(prononc)!=str:
                prononc='-'

            super_list = list()
            super_list += ['<style>._row_{display: flex;flex-direction:column ;}@media screen and (min-width: 768px) {._row_ {display:flex;flex-direction:row;}}</style>']  #-reverse
            super_list += ['<div><center style="font-size: 35px;"><b>' , lemma_word ,
                           '</b></center>  <center style="font-size: 25px;margin-top:8px;margin-bottom:13px">/',
                           prononc , '/</center></div> '] 

            super_list += ['<div class="_row_">']
            
            # Definitions
            super_list += ['<div style="width:100%;float:left">']
            super_list += ['<b><center style="font-size: 24px;font-family: Copperplate;">Definitions</center></b>']
            if translation_eng.extra_data['definitions'] != None:
                for x in translation_eng.extra_data['definitions']:
                    super_list += ['<div style="font-size:22px;font-family: Papyrus;text-align: left;direction:ltr;"><b>> ' , x[0] , ':</b></div>' ]
                    for y in x[1]:
                        super_list += ['<div style="margin-left:30px; font-size:22px;text-align: left;direction:ltr;"><li><b>' , y[0] , '</b></li></div>']


                        if len(y)> 2 and y[2]!=None:
                            super_list += ['<div style="margin-left:60px; font-size:20px;text-align: left;direction:ltr;"><i>' , y[2] , '</i></div>']
                    super_list += ['<br>']

                            
            # Synonyms
            if translation_eng.extra_data['synonyms'] != None:
                super_list += ['<br><b><center style="font-size: 24px;font-family: Copperplate;"><br>Synonyms</center></b>']
                for x in translation_eng.extra_data['synonyms']:
                    super_list += ['<div style="font-size:22px;font-family: Papyrus;text-align: left;direction:ltr;"><b>> ' , x[0] , ':</b></div>']
                    super_list += [ '<div style="margin-left:30px;text-align: left;direction:ltr;">']
                    super_list += [ " - ".join(x[1][0][0]) ]
                    super_list += ['</div><br>']
            super_list += ['</div>']


            # Translations
            if translation_target.extra_data['all-translations'] != None:
                super_list += ['<div style="width:100%;float:right;">']
                super_list += ['<b><center style="font-size: 24px;font-family: Copperplate;">Translations</center></b><br>']
                super_list += ['<table align="center"  rules="all" style="border:1.5px solid black;direction:ltr;font-size:20px;" ><tr>   <th style="text-align: center">Eng</th> <th style="text-align: center">',dest_lang,'</th>    </tr>']
                for x in translation_target.extra_data['all-translations'][0][2]:
                    super_list += ['<tr><td style="text-align:left;direction:ltr;">' , " , ".join(x[1]) , '</td><td style="text-align:right">' ,str(x[0]) , '</td></tr>']

                super_list += ['</table>'] 
                super_list += ['</div>'] 
            
            super_list += ['</div>']
            
            f1= lemma_word
            mystr = "".join(super_list)
            f2= mystr
            extra_cols=""
            if deck_name == None: deck_name=""
            if tags==None: tags=""
            file1.writelines( '<center><h1>'+f1+'</center></h1>' + '\t' + f2 + '\t' + deck_name+'\t' + tags  + '\n\n')
            
            prog_bar.setValue( prog_bar.value()+1 )


    
class GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setFixedSize(360, 400)
        self.setWindowTitle("Highlighted PDF 2 Anki FlashCards")
        self.pdf_file = ""
        self.highlights = []
        self.combobox = QComboBox()
        self.combobox.addItems(['Farsi (Persian)','Arabic','Esperanto','Spanish','German','Chinese (simplified)','Hindi','Portuguese', \
                                'Bengali','Japanese','Korean','French','Italian','Indonesian','Malay','Turkish','Ukrainian','Russian',\
                                'Bulgarian','Croatian'])
        self.lang_dict = {'Farsi (Persian)':'fa', 'Arabic':'ar', 'Esperanto':'eo' ,'Spanish':'es', 'German':'de' , \
                           'chinese (simplified)':'zh-cn', 'hindi':'Hi', 'Portuguese':'pt', 'Bengali':'bn',  'Japanese':'ja', \
                           'Korean':'ko', 'French':'fr', 'Italian':'it', 'Indonesian':'id', 'Malay':'ms', 'Turkish':'tr', \
                           'Ukrainian':'uk', 'Russian':'ru', 'Bulgarian':'bg', 'Croatian':'hr'   }
        self.deckname = None
        self.tags = None
        btn = QPushButton(self)
        btn.setText("Select a PDF file")
        btn.clicked.connect(self.open_dialog)
        
        self.l_pdf_file_name = QLabel()
        self.l_pages_scanned = QLabel()
        self.l_highlights_found = QLabel()
        self.l2 = QLabel()
        
        self.prog_bar_pages_scan = QProgressBar(self)
        self.prog_bar_pages_scan.setValue(0)
 
        self.btn_search_file = QPushButton(self)
        self.btn_search_file.setText("Scan file")
        self.btn_search_file.clicked.connect(self.btn_search_file_clicked)
        
        self.btn_choose_target_dir = QPushButton(self)
        self.btn_choose_target_dir.setText("Select Path to save generated file")
        self.btn_choose_target_dir.clicked.connect(self.btn_choose_target_dir_clicked)
        self.btn_choose_target_dir.setEnabled(False)
        
        self.cbdeck = QCheckBox()
        self.cbdeck.setCheckState(Qt.CheckState.Unchecked)
        self.cbdeck.stateChanged.connect(self.cbdeck_stateChanged)
        self.ledeck = QLineEdit()
        self.ledeck.setEnabled(False)
        
        self.cbtag = QCheckBox()
        self.cbtag.setCheckState(Qt.CheckState.Unchecked)
        self.cbtag.stateChanged.connect(self.cbtag_stateChanged)
        self.letag = QLineEdit()
        self.letag.setEnabled(False)
        
        self.btn_translate_and_generate_file = QPushButton(self)
        self.btn_translate_and_generate_file.setText("Translate and Generate file")
        self.btn_translate_and_generate_file.clicked.connect(self.btn_translate_and_generate_file_clicked)
        self.btn_translate_and_generate_file.setEnabled(False)
        
        self.prog_bar_translation = QProgressBar(self)
        self.prog_bar_translation.setValue(0)
        
        layout = QFormLayout()
        layout.addRow(btn)
        layout.addRow(self.l_pdf_file_name)
        layout.addRow(self.btn_search_file)
        layout.addRow(self.l_pages_scanned)
        layout.addRow(self.l_highlights_found)
        layout.addRow(self.prog_bar_pages_scan) 
        
        layout.addRow(self.btn_choose_target_dir)
        layout.addRow(self.l2)
        
        layout.addRow(self.combobox) #self.combobox.currentText()
        layout.addRow(self.cbdeck , QLabel('Dock:'))
        layout.addRow(self.ledeck)
        layout.addRow(self.cbtag , QLabel('Tag:'))
        layout.addRow(self.letag)
        layout.addRow(self.btn_translate_and_generate_file)
        layout.addRow(self.prog_bar_translation)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)
        
    def btn_choose_target_dir_clicked(self):
        self.target_dir = QFileDialog.getExistingDirectory(self,"Exportar relatório...", "" ,QFileDialog.Option.DontUseNativeDialog )
        self.l2.setText( self.target_dir +  os.sep  + self.pdf_file_name.replace('.pdf','___FlashCards.txt' )  )
        self.btn_translate_and_generate_file.setEnabled(True)
    
    def open_dialog(self):
        self.pdf_file = QFileDialog.getOpenFileName(self,"...", "" , "PDF (*.pdf);")  
        self.btn_translate_and_generate_file.setEnabled(False)
        self.btn_choose_target_dir.setEnabled(False)

        
        
        self.pdf_file_path, self.pdf_file_name = os.path.split(self.pdf_file[0])
        self.l_pdf_file_name.setText( self.pdf_file_name )
        # print(self.fname[0])
        # input_file_path = self.fname[0]
        
    
    def btn_search_file_clicked(self):
        try:
            self.prog_bar_pages_scan.setValue(0)
            self.highlights,total_pages_scanned = find_highlighted_words(self.pdf_file[0] , self.prog_bar_pages_scan)
            self.l_pages_scanned.setText(str(total_pages_scanned) + ' pages scanned' )
            self.l_highlights_found.setText(str(len(self.highlights)) + ' highlights were found')
            # print(self.highlights )
            if len(self.highlights) > 0:
                self.prog_bar_translation.setRange(0, len(self.highlights) )
                self.btn_choose_target_dir.setEnabled(True)
            else: 
                button = QMessageBox.critical(self,"Something went wrong!","No highlight was found!") 
        except Exception as e:
            button = QMessageBox.critical(self,"Something went wrong!",str(e))    
        
    def btn_translate_and_generate_file_clicked(self):
        try:
            if self.cbdeck.isChecked() and self.ledeck.text()!="": self.deckname=self.ledeck.text()
            else: self.deckname= None
            if self.cbtag.isChecked() and self.letag.text()!="": self.tags = self.letag.text()
            else: self.tags= None
            self.prog_bar_translation.setValue(0)
            dest_lang_code = self.lang_dict[ self.combobox.currentText() ]
            
            Translate_and_Write_file(self.highlights , target_file_name=self.l2.text() , dest_lang=dest_lang_code , prog_bar=self.prog_bar_translation,deck_name=self.deckname,tags=self.tags)
            
            
            button = QMessageBox.information(self,"Successful",self.l2.text())
            
        except Exception as e:
            button = QMessageBox.critical(self,"Something went wrong!",str(e))
            
    def cbdeck_stateChanged(self):
        self.ledeck.setEnabled(self.cbdeck.isChecked())
        
        
    def cbtag_stateChanged(self):
        self.letag.setEnabled( self.cbtag.isChecked())
        
        
def run():
    app = QApplication(sys.argv)
    main_gui = GUI()
    main_gui.show()
    sys.exit(app.exec())
    run()
    
    
