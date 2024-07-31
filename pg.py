def import_data(client,data,collection_name):
    qa_collection = client.collections.get(collection_name)
    counter = 0
    interval = 1000
    with qa_collection.batch.dynamic() as batch:
        for d in data:
            for doc in d["documents"]:
                try:
                    properties={
                        "doc_id": doc["doc_id"],
                        "question": d["question"],
                        "answer": d["answer"],
                        "title": doc["title"],
                        "text": doc["text"]
                        }

                    obj_uuid = weaviate.util.generate_uuid5(doc["doc_id"])
                    batch.add_object(uuid=obj_uuid,
                                    properties=properties)
                    counter += 1
                    if counter % interval == 0:
                        logger.info(f"Inserted {counter} documents so far.")
                except Exception as e:
                    logger.error(f"Error inserting document with UUID: {obj_uuid}: {str(e)}")

    failed_objs_b = qa_collection.batch.failed_objects
    if failed_objs_b:
        logger.error(f"Failed objects: {failed_objs_b}") 
    # qa_collection.data.insert_many(qa_data_objs)
    total_count = qa_collection.aggregate.over_all(total_count=True).total_count
    logger.info(f"Total successful count: {total_count}")
    return qa_collection