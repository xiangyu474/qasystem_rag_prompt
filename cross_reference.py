import weaviate
import weaviate.classes.config as wvcc
from weaviate.util import generate_uuid5
from weaviate.exceptions import WeaviateBaseError
from weaviate.classes.data import DataReference

######## CONSTANTS
ART_COLL_NAME_STR = "ArticlesTest"
ENT_COLL_NAME_STR = "EntitiesTest"
CROSS_PROPERTY_NAME = "hasEntities"
BM25_PARAMS = {
    "bm25_b": 0.75,
    "bm25_k1": 1.2,
    "cleanup_interval_seconds": 60,
    "index_timestamps": False,
    "index_property_length": False,
    "index_null_state": False,
    "stopwords_preset": None,
    "stopwords_additions": ["di", "a", "da", "in", "con", "su", "per", "tra", "fra"],
    "stopwords_removals": None,
}

wv_client = weaviate.connect_to_embedded()

######## Define the entities and articles collections
# ENT_COLL_NAME_STR -> Documents : doc_id-title-text
wv_client.collections.delete(ENT_COLL_NAME_STR)
wv_client.collections.create(
    name=ENT_COLL_NAME_STR,
    description="A collection of entities with their own properties",
    vectorizer_config=None,
    properties=[
        wvcc.Property(
            name="entity_id",
            data_type=wvcc.DataType.TEXT,
            skip_vectorization=True,
        ),
        wvcc.Property(
            name="entitytext",
            data_type=wvcc.DataType.TEXT,
            skip_vectorization=True,
        ),
        wvcc.Property(
            name="IQ",
            data_type=wvcc.DataType.INT,
        ),
    ],
)


######## Define the Articles collection with a cross-reference to an Entities collection; custom non English list of stopwords
# ART_COLL_NAME_STR -> QnA : query-answer-cited document([]) -> 引用ENT_COLL_NAME_STR
wv_client.collections.delete(ART_COLL_NAME_STR)
wv_client.collections.create(
    name=ART_COLL_NAME_STR,
    description="A collection of Articles with only a custom list of stopwords",
    vectorizer_config=None,
    inverted_index_config=wvcc.Configure.inverted_index(**BM25_PARAMS),
    properties=[
        wvcc.Property(
            name="articleid",
            data_type=wvcc.DataType.TEXT,
            skip_vectorization=True,
        ),
        wvcc.Property(
            name="articletext",
            data_type=wvcc.DataType.TEXT,
        ),
    ],
    references=[
        wvcc.ReferenceProperty(
            name=CROSS_PROPERTY_NAME, target_collection=ENT_COLL_NAME_STR
        )
    ],
)

######## fill some data in the entities collections
entities_data = [
    {"entity_id": 1, "entity_text": "Bob", "IQ": 200},
    {"entity_id": 2, "entity_text": "Guido", "IQ": 164},
    {"entity_id": 3, "entity_text": "Aldo", "IQ": 120},
    {"entity_id": 4, "entity_text": "Carlo", "IQ": 144},
]
wv_entcoll = wv_client.collections.get(ENT_COLL_NAME_STR)
try:
    for entity in entities_data:
        ENTITY_UUID = generate_uuid5(entity["ID"])
        if (
            wv_entcoll.query.fetch_object_by_id(ENTITY_UUID) is None
        ):  # do not duplicate entities
            collection_uuid = wv_entcoll.data.insert(
                properties=entity, uuid=ENTITY_UUID
            )
except WeaviateBaseError as error:
    print(f"Weaviate error: {error.message}")

######## now add two Articles from the following data:
# ART_COLL_NAME_STR -> QnA : query-answer-cited document([])
articles_data = [
    {
        "articleid": "primo-articolo",
        "articletext": "La formazione dei geni",
        "entities": [1, 2],
    },
    {
        "articleid": "secondo_articolo",
        "articletext": "Non ci posso credere",
        "entities": [1, 3, 4],
    },
]
wv_artcoll = wv_client.collections.get(ART_COLL_NAME_STR)
try:
    for article in articles_data:
        ARTICLE_UUID = generate_uuid5(article["articleid"])
        if (
            wv_entcoll.query.fetch_object_by_id(ARTICLE_UUID) is None
        ):  # do not duplicate
            properties_data = {
                key: article[key] for key in ["articleid", "articletext"]
            }  # isolate the Articles class properties only
            collection_uuid = wv_artcoll.data.insert(
                properties=properties_data, uuid=ARTICLE_UUID
            )  # add the article object
            # An article can have MULTIPLE references to different entitities build and add them
            refs_list = []
            for entityID in article["entities"]:
                ENTITY_UUID = generate_uuid5(entityID)
                ref_object = DataReference(
                    from_uuid=ARTICLE_UUID,
                    from_property=CROSS_PROPERTY_NAME,
                    to_uuid=ENTITY_UUID,
                )
                refs_list.append(ref_object)
            wv_artcoll.data.reference_add_many(refs_list)
except WeaviateBaseError as error:
    print(f"Weaviate error: {error.message}")

wv_client.close()