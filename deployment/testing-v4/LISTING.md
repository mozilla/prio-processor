# Directory listing

This listing was generated from `scripts/list-bucket`. It is a list of all
objects stored across the the two servers.

## Server A buckets

### `gs://a-ingest-d70d758a4b28a791/`

```
.
└── gs:
    └── a-ingest-d70d758a4b28a791
        └── test-app
            └── v1
                └── C629C221FBCF524FE2FC746A0E114749DF18013F893280B4203F20859CA7FC4B
                    └── test-app
                        └── 2021-04-27
                            └── raw
                                └── shares
                                    ├── _SUCCESS
                                    ├── batch_id=bad-id
                                    │   └── part-00000-90dbdd61-fb92-4fc0-839f-94e498118b03.c000.json
                                    └── batch_id=content.blocking_blocked_TESTONLY-0
                                        └── part-00001-90dbdd61-fb92-4fc0-839f-94e498118b03.c000.json

11 directories, 3 files
```

### `gs://a-private-d70d758a4b28a791/`

```
.
└── gs:
    └── a-private-d70d758a4b28a791
        └── test-app
            └── v1
                └── C629C221FBCF524FE2FC746A0E114749DF18013F893280B4203F20859CA7FC4B
                    └── test-app
                        └── 2021-04-27
                            ├── intermediate
                            │   └── internal
                            │       ├── aggregate
                            │       │   └── batch_id=content.blocking_blocked_TESTONLY-0
                            │       │       ├── _SUCCESS
                            │       │       └── part-00000-f5aade7b-b173-40ae-ab1f-8227320cd21c-c000.json
                            │       ├── verify1
                            │       │   └── batch_id=content.blocking_blocked_TESTONLY-0
                            │       │       ├── _SUCCESS
                            │       │       ├── part-00000-4cce36b2-a0be-4d47-8a97-70a5909325c2-c000.json
                            │       │       └── part-00001-4cce36b2-a0be-4d47-8a97-70a5909325c2-c000.json
                            │       └── verify2
                            │           └── batch_id=content.blocking_blocked_TESTONLY-0
                            │               ├── _SUCCESS
                            │               ├── part-00000-87589739-465a-4c4b-8329-8d4be400bf6f-c000.json
                            │               └── part-00001-87589739-465a-4c4b-8329-8d4be400bf6f-c000.json
                            └── processed
                                └── publish
                                    └── batch_id=content.blocking_blocked_TESTONLY-0
                                        ├── _SUCCESS
                                        └── part-00000-806a39fe-12e8-42d2-9a2d-763ac21da8bb-c000.json

18 directories, 10 files
```

### `gs://a-shared-d70d758a4b28a791/`

```
.
└── gs:
    └── a-shared-d70d758a4b28a791
        └── test-app
            └── v1
                └── C629C221FBCF524FE2FC746A0E114749DF18013F893280B4203F20859CA7FC4B
                    └── test-app
                        └── 2021-04-27
                            └── intermediate
                                └── external
                                    ├── aggregate
                                    │   ├── _SUCCESS
                                    │   └── batch_id=content.blocking_blocked_TESTONLY-0
                                    │       ├── _SUCCESS
                                    │       └── part-00000-e74badbf-9ab5-4e62-9238-b368f881b7a9-c000.json
                                    ├── verify1
                                    │   ├── _SUCCESS
                                    │   └── batch_id=content.blocking_blocked_TESTONLY-0
                                    │       ├── _SUCCESS
                                    │       └── part-00000-6f55cefd-c443-4d08-b179-9cff80903fa3-c000.json
                                    └── verify2
                                        ├── _SUCCESS
                                        └── batch_id=content.blocking_blocked_TESTONLY-0
                                            ├── _SUCCESS
                                            └── part-00000-1a7a7d5b-f0d5-4eb3-a6b0-f2876117f1c3-c000.json

15 directories, 9 files
```

## Server B buckets

### `gs://b-ingest-d70d758a4b28a791/`

```
.
└── gs:
    └── b-ingest-d70d758a4b28a791
        └── test-app
            └── v1
                └── E58761F983D681367F854C4DE70D2BFA7BE6CDE79422B57B4B850ABD7FCB6839
                    └── test-app
                        └── 2021-04-27
                            └── raw
                                └── shares
                                    ├── _SUCCESS
                                    ├── batch_id=bad-id
                                    │   └── part-00000-90dbdd61-fb92-4fc0-839f-94e498118b03.c000.json
                                    └── batch_id=content.blocking_blocked_TESTONLY-0
                                        └── part-00001-90dbdd61-fb92-4fc0-839f-94e498118b03.c000.json

11 directories, 3 files
```

### `gs://b-private-d70d758a4b28a791/`

```
.
└── gs:
    └── b-private-d70d758a4b28a791
        └── test-app
            └── v1
                └── E58761F983D681367F854C4DE70D2BFA7BE6CDE79422B57B4B850ABD7FCB6839
                    └── test-app
                        └── 2021-04-27
                            ├── intermediate
                            │   └── internal
                            │       ├── aggregate
                            │       │   └── batch_id=content.blocking_blocked_TESTONLY-0
                            │       │       ├── _SUCCESS
                            │       │       └── part-00000-e74badbf-9ab5-4e62-9238-b368f881b7a9-c000.json
                            │       ├── verify1
                            │       │   └── batch_id=content.blocking_blocked_TESTONLY-0
                            │       │       ├── _SUCCESS
                            │       │       └── part-00000-6f55cefd-c443-4d08-b179-9cff80903fa3-c000.json
                            │       └── verify2
                            │           └── batch_id=content.blocking_blocked_TESTONLY-0
                            │               ├── _SUCCESS
                            │               └── part-00000-1a7a7d5b-f0d5-4eb3-a6b0-f2876117f1c3-c000.json
                            └── processed
                                └── publish
                                    └── batch_id=content.blocking_blocked_TESTONLY-0
                                        ├── _SUCCESS
                                        └── part-00000-a7e8122c-3f79-4d3c-88be-7d08c6863a72-c000.json

18 directories, 8 files
```

### `gs://b-shared-d70d758a4b28a791/`

```
.
└── gs:
    └── b-shared-d70d758a4b28a791
        └── test-app
            └── v1
                └── E58761F983D681367F854C4DE70D2BFA7BE6CDE79422B57B4B850ABD7FCB6839
                    └── test-app
                        └── 2021-04-27
                            └── intermediate
                                └── external
                                    ├── aggregate
                                    │   ├── _SUCCESS
                                    │   └── batch_id=content.blocking_blocked_TESTONLY-0
                                    │       ├── _SUCCESS
                                    │       └── part-00000-f5aade7b-b173-40ae-ab1f-8227320cd21c-c000.json
                                    ├── verify1
                                    │   ├── _SUCCESS
                                    │   └── batch_id=content.blocking_blocked_TESTONLY-0
                                    │       ├── _SUCCESS
                                    │       ├── part-00000-4cce36b2-a0be-4d47-8a97-70a5909325c2-c000.json
                                    │       └── part-00001-4cce36b2-a0be-4d47-8a97-70a5909325c2-c000.json
                                    └── verify2
                                        ├── _SUCCESS
                                        └── batch_id=content.blocking_blocked_TESTONLY-0
                                            ├── _SUCCESS
                                            ├── part-00000-87589739-465a-4c4b-8329-8d4be400bf6f-c000.json
                                            └── part-00001-87589739-465a-4c4b-8329-8d4be400bf6f-c000.json

15 directories, 11 files
```

