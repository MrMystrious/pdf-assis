import fitz
import nltk
import string
import pytesseract
import io
import re
import spacy
import json
import math
import time
from nltk.tokenize import sent_tokenize
from PIL import Image
from concurrent.futures import ThreadPoolExecutor,as_completed

nltk.download('punkt')
nlp = spacy.load("en_core_web_sm")

import time

class getPage:
    def __init__(self):
        pass

    def preprocess(self, txt):
        start = time.time()
        txt = txt.lower()
        txt = txt.replace('\n',' ')
        txt = re.sub(r'[\u2022\u2023\u25E6\u2043\u2219\uf0d8\n\uf0d8]', '. ', txt)
        txt = re.sub(r'[\uf000-\uf0ff]', '', txt)
        txt = txt.replace('\n•', '[BULLET]')
        txt = re.sub(r'\s+', ' ', txt).strip()
        txt = re.sub(r'[^A-Za-z0-9.,;:!?@#&%()\-\s]', ' ', txt)
        txt = ' '.join(txt.split())
        sentence_tok = sent_tokenize(txt)
        sentences = [s for s in sentence_tok if s.strip()]
       # print(f"[preprocess] took {time.time() - start:.3f}s")
        return sentences

    def get_images(self, images, pdf, page_num=None, total_pages=None):
        start_total = time.time()
        ocr_txt = []

        print(f"[OCR] Found {len(images)} image(s) on page {page_num}/{total_pages}.")

        for i, img in enumerate(images, start=1):
            img_start = time.time()
            print(f"   [OCR] Processing image {i}/{len(images)} on page {page_num} ...")

            xref = img[0]
            base_img = pdf.extract_image(xref)
            image = Image.open(io.BytesIO(base_img['image']))
            image = image.convert('L')
            image = image.point(lambda x: 0 if x < 140 else 255)

            text = pytesseract.image_to_string(image, config='--oem 3 --psm 6')
            preprocess_text = self.preprocess(text)
            ocr_txt.extend(preprocess_text)

            print(f"   [OCR] Image {i} on page {page_num} done in {time.time() - img_start:.2f}s")

        print(f"[OCR] Page {page_num} OCR total took {time.time() - start_total:.2f}s\n")
        return ocr_txt


    def extract_entity(self, text):
        start = time.time()
        doc = nlp(text)
        entities = [ent.text for ent in doc.ents if ent.label_ not in ['CARDINAL', 'ORDINAL']]
        relationships = []
        for token in doc:
            if token.pos_ in ["PROPN", "NOUN"]:
                entities.append(token.text.lower())
        for sent in doc.sents:
            subj, verb, obj = None, None, None
            for token in sent:
                if token.dep_ == "nsubj":
                    subj = token.text
                if token.pos_ == "VERB":
                    verb = token.text
                if token.dep_ in ["dobj", "attr", "pobj", "iobj"]:
                    obj = token.text
                if subj and verb and obj:
                    relationships.append((subj, verb, obj))
                    subj, verb, obj = None, None, None
       # print(f"[extract_entity] took {time.time() - start:.3f}s")
        return entities, relationships
    
    def get_pdfPages(self, path, chuck_size=300, overlap_sentence=5, max_chunks=1000):
        total_start = time.time()
        print("extractor running...")
        pdf = fitz.open(path)
        docs, chucks = [], []

        # ---------- PAGE TEXT EXTRACTION (PARALLEL) ----------
        start = time.time()

        def extract_page(num):
            page_start = time.time()
    #        print(f"[INFO] Processing page {num+1}/{len(pdf)} ...")
            page = pdf.load_page(num)
            text = page.get_text("text")
    #        print(f"[DONE] Page {num+1} processed in {time.time() - page_start:.2f}s")
            return num, text

        texts = [None] * len(pdf)
        with ThreadPoolExecutor() as ex:
            futures = [ex.submit(extract_page, i) for i in range(len(pdf))]
            for future in as_completed(futures):
                num, text = future.result()
                texts[num] = text

        print(f"[text extraction (all pages)] took {time.time() - start:.3f}s")

        # ---------- PREPROCESS + OCR ----------
        start = time.time()
        for i, text in enumerate(texts):
            if text.strip():
                docs.extend(self.preprocess(text))
            else:
                images = pdf.load_page(i).get_images(full=True)
                if images:
                    docs.extend(self.get_images(images, pdf, page_num=i+1, total_pages=len(pdf)))
        print(f"[preprocessing + OCR] took {time.time() - start:.3f}s")
        print("doc size:", len(docs))

        # ---------- CHUNK CREATION ----------
        start = time.time()
        current_chk, chunks_texts, current_len = [], [], 0
        print("\n[INFO] Starting chunk creation...")

        for idx, sen in enumerate(docs):
            sen_len = len(sen)
            if current_len + sen_len < chuck_size:
                current_chk.append(sen)
                current_len += sen_len
            else:
                txt = ' '.join(current_chk)
                chunks_texts.append(txt)
                print(f"   [CHUNK CREATED] #{len(chunks_texts)} → {len(current_chk)} sentences, {current_len} chars")
                current_chk = current_chk[-overlap_sentence:] + [sen]
                current_len = sum(len(s) for s in current_chk)

        if current_chk:
            txt = ' '.join(current_chk)
            chunks_texts.append(txt)
    #        print(f"   [CHUNK CREATED] #{len(chunks_texts)} → {len(current_chk)} sentences, {current_len} chars")

    #    print(f"[chunking only] took {time.time() - start:.3f}s")
    #    print(f"Total chunks to process: {len(chunks_texts)}")

        # ---------- FORCE APPROX 5000 CHUNKS ----------
        if len(chunks_texts) > max_chunks:
            merge_factor = math.ceil(len(chunks_texts) / max_chunks)
    #        print(f"[INFO] Merging chunks: {len(chunks_texts)} → {max_chunks} (merge_factor={merge_factor})")
            merged = []
            for i in range(0, len(chunks_texts), merge_factor):
                merged.append(' '.join(chunks_texts[i:i+merge_factor]))
            chunks_texts = merged

        elif len(chunks_texts) < max_chunks:
    #        print(f"[INFO] Splitting large chunks to reach ~{max_chunks} total")
            subdivided = []
            avg_len = sum(len(c) for c in chunks_texts) // max_chunks if max_chunks > 0 else 1
            for c in chunks_texts:
                if len(c) > avg_len * 1.5:  # only split big chunks
                    for i in range(0, len(c), avg_len):
                        subdivided.append(c[i:i+avg_len])
                else:
                    subdivided.append(c)
            chunks_texts = subdivided[:max_chunks]

        print(f"[INFO] Final chunk count: {len(chunks_texts)}")

        # ---------- PARALLEL ENTITY EXTRACTION ----------
        start_entity = time.time()

        def process_chunk(chunk_info):
            i, txt = chunk_info
            entity, relation = self.extract_entity(txt)
        #    print(f"   [ENTITY EXTRACTION DONE] Chunk #{i+1} ({len(txt)} chars)")
            return {
                'chunk_id': i+1,
                'sentence_count': len(sent_tokenize(txt)),
                'text': txt,
                'entity': entity,
                'relation': relation
            }

        with ThreadPoolExecutor() as ex:
            chucks = list(ex.map(process_chunk, enumerate(chunks_texts)))

        print(f"[entity extraction (parallel)] took {time.time() - start_entity:.3f}s")
        print(f"[chunking + entity extraction total] {time.time() - start:.3f}s")
        print(f"[total get_pdfPages time] {time.time() - total_start:.3f}s")

        return chucks


    """ def get_pdfPages(self,path,chuck_size=300,overlap_sentence = 5):
        total_start = time.time()
        print("extractor running...")
        pdf = fitz.open(path)
        docs = []
        chucks = []
        #print(f'\n\n{fitz.get_text(path)}\n\n')
        for pages in pdf:
            page = pages.get_text('text')
            doc = self.preprocess(page) if page else []
            ocr_text = []
            if not page.strip():
                images = pages.get_images(full=True)
                if images:
                    ocr_text = self.get_images(images, pdf)
            if doc:
                docs.extend(doc)
            if ocr_text:
                docs.extend(ocr_text)
        current_chk = []
        start = time.time()
        for sen in docs:
            if sum(len(s) for s in current_chk) + len(sen) < chuck_size:
                current_chk.append(sen)
            else:
                txt = ' '.join(current_chk)
                entity,relation = self.extract_entity(txt)
                chucks.append({
                    'text':txt,
                    'entity':entity,
                    'relation':relation
                })
                current_chk = current_chk[-overlap_sentence:]+[sen]
        if current_chk:
            txt = ' '.join(current_chk)
            entity,relation = self.extract_entity(txt)
            chucks.append({
                'text':txt,
                'entity':entity,
                'relation':relation
            })
        print(f"[chunking + entity extraction] took {time.time() - start:.3f}s")
        print(f"[total get_pdfPages time] {time.time() - total_start:.3f}s")

        return chucks
 """
#path = r'C:\Users\Balaji\Documents\vs-prac\pdfEditor12\src\mcPdf.pdf'
""" g = getPage()
chk = g.get_pdfPages(path,chuck_size=500,overlap_sentence=1)
with open('page.json','w',encoding='utf-8') as f:
    json.dump(chk,f,indent=2) """