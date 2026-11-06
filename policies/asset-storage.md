# Asset storage

Initial publication includes **zero media binaries**. Keep public, factual link metadata separate from permissions. PDFs and rendered slides in the application remain excluded until exact source reproduction/redistribution/adaptation rights and review are established.

Ordinary Git may hold individually reviewed assets up to 1 MiB each. This bounds the initial policy; it is not a source copyright or technical quality judgment. Local assets require registered MediaAsset identity/revision, exact file path, byte size, SHA-256, MIME/extension and verifiable signature. The initial signature adapters cover PDF, PNG, JPEG, WebP, WAV and UTF-8 plain text. Unsupported formats fail closed until an adapter and storage decision are reviewed. Declared local files must exist; unregistered assets and unsafe paths fail. Public local files need independently approved redistribution rights even while drafting.

Large video/audio normally stays externally hosted; do not download or copy streams. External URL metadata may omit unknown stream MIME, length, size and checksum. A YouTube page URL is not evidence of an MP4 format, available captions or permission. Stable HTTPS links must contain no credentials or token queries. Offline validation never fetches a remote URL or treats it as a grant.

No Git LFS is introduced: there are no published binaries and no demonstrated need. A later LFS decision must cover clone/checkout requirements, quota/bandwidth costs, CI access, pointer/file verification and archive availability. There is no object-storage service or application-specific media dependency. Moving storage changes a MediaAsset revision/location, not the logical Resource’s identity.
