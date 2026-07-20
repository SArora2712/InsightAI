"""
Extarcts clean text along with perpage metadate from pdf document so downstream chunking/embedding 
steps can preserve source attributtion(doc name, page number)

"""
from dataclasses import dataclass,field
from pathlib import Path
from typing import List
import fitz

@dataclass 
class PageContent:
    doc_name:str
    page_number:int
    text:str

@dataclass
class ParsedDocument:
    doc_name:str
    source_path:str
    pages:List[PageContent]=field(default_factory=list)

    @property
    def full_text(self)->str:
        return "\n\n".join(p.text for p in self.pages)
    

def parse_pdf(file_path:str)->ParsedDocument:
    path=Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"No File Found at {file_path}")
    doc_name=path.stem
    pages:List[PageContent]=[]

    with fitz.open(str(path)) as pdf:
        for i,page in enumerate(pdf,start=1):
            text=page.get_text("text").strip()
            if text:
                pages.append(PageContent(doc_name=doc_name,page_number=i,text=text))

    return ParsedDocument(doc_name=doc_name,source_path=str(path),pages=pages)


def parse_directory(dir_path:str)->List[ParsedDocument]:
    """ Parse every pdf in directory"""
    dir_p=Path(dir_path)
    results=[]
    for pdf_file in sorted(dir_p.glob("*.pdf")):
        results.append(parse_pdf(str(pdf_file)))
    return results

if __name__=="__main__":
    docs=parse_directory("data/raw")
    for d in docs:
        print(f"\n==={d.doc_name} ({len(d.pages)} pages)===")
        for p in d.pages:
            preview=p.text[:120].replace("\n","")
            print(f"Page {p.page_number}:{preview}")

