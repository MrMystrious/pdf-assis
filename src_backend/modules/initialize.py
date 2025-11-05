from src.modules.extractor import getPage
from src.modules.embedd import VecDB
from src.modules.knowedge_graph import KG
from src.modules.chat import Chat
import json

class Initialize:
    def __init__(self, path: str, id: str = "", dbname: str = "my-db", manageConnection=None):
        from src.server import ConnectionManager
        self.conn = manageConnection or ConnectionManager()
        self.path = path
        self.id = id
        self.dbname = dbname

        # Placeholders for async components
        self.pdf = None
        self.kg = None
        self.db = None
        self.chat = None

    async def init(self):
        print("Initializing PDF object...")
        self.pdf = getPage()
        await self.conn.send_personal_message("Initializing PDF object...", self.id, "uploadStatus")

        print("Initializing Knowledge Graph...")
        self.kg = KG()

        print("Initializing Database...")
        self.db = VecDB(db_name=self.dbname)
        await self.conn.send_personal_message("Initializing Vector DB...", self.id, "uploadStatus")

        print("Initializing Chat UI...")
        self.chat = Chat()
        self.chat.build_graph([('chat', self.chat.chat_node)])
        await self.conn.send_personal_message("Building Graph...", self.id, "uploadStatus")

        print("All components are initialized!")
        return self 

    async def analyze_page(self, chuck=400, over=2, max_chunck=500) -> None:
        try:
            print("__chunks-creating__")
            pdf = self.pdf.get_pdfPages(self.path, chuck_size=chuck, overlap_sentence=over, max_chunks=max_chunck)
            await self.conn.send_personal_message("Getting PDF pages...", self.id, "uploadStatus")

            self.kg.build_kg(pdf)
            await self.conn.send_personal_message("Building KG...", self.id, "uploadStatus")

            print("__Knowledge-Graph__")
            self.db.save_to_chroma(pdf)
            await self.conn.send_personal_message("Saving to DB...", self.id, "uploadEnd")

            print("__Saved-in-DB__")
        except Exception as e:
            print(f"Error in analyze_page: {e}")

    async def query(self, q: str, k: int):
        q = self.pdf.preprocess(q)[0]
        await self.conn.send_personal_message("query Preprocessed", self.id, "queryProcessed")
        ent, rel = self.pdf.extract_entity(q)
        await self.conn.send_personal_message("Entity Processed", self.id, "queryProcessed")
        nodes, edges = self.kg.match_queries(ent, rel)
        await self.conn.send_personal_message("Nodes and edges Processed", self.id, "queryProcessed")
        result = self.db.query_with_kg_filter(q, nodes, edges, k=k)
        await self.conn.send_personal_message("KG Quey Processed", self.id, "queryProcessed")
        with open('page.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)

        text = ""
        for doc in result.get('documents', [''])[0]:
            text += doc

        text += (" " * 26)
        text += "<query>" + q + "</query>"
        await self.conn.send_personal_message("Query Processed", self.id, "queryProcessed")
        for tok in self.chat.getResult(text):
            yield tok
