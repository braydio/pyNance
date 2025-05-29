[CHROMA] Running index update after commit...
g[CHROMA] Connecting to Chroma server at http://localhost:8000
iTraceback (most recent call last):
File "/home/braydenchaffee/Projects/pyNance/scripts/chroma_index.py", line 41, in <module>
collection.add(
~~~~~~~~~~~~~~^
documents=[chunk], metadatas=[{"source": path}], ids=[doc_id]
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
)
^
File "/home/braydenchaffee/Projects/pyNance/.venv/lib/python3.13/site-packages/chromadb/api/models/Collection.py", line 89, in add
self.\_client.\_add(
~~~~~~~~~~~~~~~~~^
collection_id=self.id,
^^^^^^^^^^^^^^^^^^^^^^
...<6 lines>...
database=self.database,
^^^^^^^^^^^^^^^^^^^^^^^
)
^
File "/home/braydenchaffee/Projects/pyNance/.venv/lib/python3.13/site-packages/chromadb/telemetry/opentelemetry/**init**.py", line 150, in wrapper
return f(\*args, \*\*kwargs)
File "/home/braydenchaffee/Projects/pyNance/.venv/lib/python3.13/site-packages/chromadb/api/fastapi.py", line 516, in \_add
self.\_submit_batch(
~~~~~~~~~~~~~~~~~~^
batch,
^^^^^^
f"/tenants/{tenant}/databases/{database}/collections/{str(collection_id)}/add",
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
)
^
File "/home/braydenchaffee/Projects/pyNance/.venv/lib/python3.13/site-packages/chromadb/telemetry/opentelemetry/**init**.py", line 150, in wrapper
return f(\*args, \*\*kwargs)
File "/home/braydenchaffee/Projects/pyNance/.venv/lib/python3.13/site-packages/chromadb/api/fastapi.py", line 479, in \_submit_batch
self.\_make_request(
~~~~~~~~~~~~~~~~~~^
"post",
^^^^^^^
...<7 lines>...
},
^^
)
^
File "/home/braydenchaffee/Projects/pyNance/.venv/lib/python3.13/site-packages/chromadb/api/base_http_client.py", line 97, in \_raise_chroma_errorr
raise chroma_error
chromadb.errors.InternalError:Query error: Database error: error returned from database: (code: 1032) attempt to write a readonly database
