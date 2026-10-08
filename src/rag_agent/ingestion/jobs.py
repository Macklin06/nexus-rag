from dataclasses import dataclass


@dataclass(frozen=True)
class IngestionJob:
    document_version_id: int

    def to_payload(self) -> str:
        return str(self.document_version_id)

    @classmethod
    def from_payload(cls, payload: str) -> "IngestionJob":
        try:
            document_version_id = int(payload)
        except ValueError as exc:
            raise ValueError(
                f"Invalid ingestion job payload: {payload!r}"
            ) from exc

        if document_version_id <= 0:
            raise ValueError(
                "document_version_id must be greater than 0"
            )

        return cls(document_version_id=document_version_id)