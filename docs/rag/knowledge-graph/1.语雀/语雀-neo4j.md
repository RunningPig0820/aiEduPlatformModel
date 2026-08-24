# neo4j（语雀原稿）

> 来源：https://www.yuque.com/zhangmin-jrrer/iu9s4m/av0vhqyn7rgx8rni
> 字数：52 ｜ 下载：2026-08-24

```plain
docker stop neo4j
docker rm neo4j

docker run -d \
  --name neo4j \
  --restart always \
  -p 7474:7474 \
  -p 7687:7687 \
  -v /data/neo4j/data:/data \
  -v /data/neo4j/logs:/logs \
  -e NEO4J_ACCEPT_LICENSE_AGREEMENT=yes \
  -e NEO4J_AUTH=neo4j/Neo4j_2025@Edu \
  -e NEO4J_server_memory_heap_initial__size=2G \
  -e NEO4J_server_memory_heap_max__size=2G \
  -e NEO4J_server_memory_pagecache_size=1G \
  -e NEO4J_server_https_enabled=false \
  -e NEO4J_server_config_strict__validation_enabled=false \
  neo4j:5-enterprise
```