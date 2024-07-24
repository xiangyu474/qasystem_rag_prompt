import weaviate
from weaviate.connect import ConnectionParams
from weaviate.classes.init import AdditionalConfig, Timeout
import os
# ???WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
# I0000 00:00:1721787103.899938   22508 config.cc:230] gRPC experiments enabled: call_status_override_on_cancellation, event_engine_client, event_engine_dns, event_engine_listener, http2_stats_fix, monitoring_experiment, pick_first_new, trace_record_callops, work_serializer_clears_time_cache
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

client = weaviate.connect_to_local()

print(client.is_ready())
client.close()