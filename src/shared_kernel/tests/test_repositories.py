"""Tests für IUserOwned-Integration und Optimistic-Concurrency-Control."""

from dataclasses import dataclass
from typing import final
from uuid import UUID, uuid4, uuid7

import pytest

from src.shared_kernel.concurrency import ConcurrencyConflictError, RowVersion
from src.shared_kernel.result import Err, Ok

# ============================================================================
# Test Fixtures: Dummy Aggregate mit User-Ownership
# ============================================================================


@final
@dataclass(frozen=True, slots=True)
class DummyNote:
    """Dummy-Aggregate zum Testen: eine Notiz mit User-Ownership.

    Erfüllt das IUserOwned-Protocol durch strukturelles Typing
    (deklariert user_id: UUID direkt als Feld).
    """

    id: UUID
    user_id: UUID
    title: str
    content: str
    row_version: RowVersion


# ============================================================================
# Test Repository mit IUserOwned-Filtering
# ============================================================================


@final
class InMemoryDummyNoteRepository:
    """Test-Repository für DummyNote mit User-Isolation via IUserOwned.

    Speichert Noten im Memory (nur für Tests) und filtert auf UserId
    beim Abrufen, um Datenlecks zwischen Users zu verhindern.
    """

    def __init__(self) -> None:
        """Initialisiere das Repository."""
        self._notes: dict[UUID, DummyNote] = {}
        self._xmin_counter: int = 1

    def create(self, user_id: UUID, title: str, content: str) -> DummyNote:
        """Erstelle eine neue Note.

        Args:
            user_id: Die UUID des Besitzers.
            title: Titel der Note.
            content: Inhalt der Note.

        Returns:
            Die neu erstellte DummyNote mit initialer RowVersion.
        """
        note_id = uuid7()
        row_version = RowVersion.from_xmin(self._xmin_counter)
        self._xmin_counter += 1
        note = DummyNote(
            id=note_id,
            user_id=user_id,
            title=title,
            content=content,
            row_version=row_version,
        )
        self._notes[note_id] = note
        return note

    def get_by_id(self, note_id: UUID, requesting_user_id: UUID) -> DummyNote | None:
        """Hole eine Note nach ID, gefiltert auf requesting_user_id.

        KRITISCH: Dieses Repository implementiert User-Isolation durch
        Filterung auf UserId. Eine Query liefert nur Notes, deren user_id
        gleich requesting_user_id ist. Damit wird ein Datenleak zwischen
        Users verhindert.

        Args:
            note_id: Die ID der abzurufenden Note.
            requesting_user_id: Die UUID des anfragenden Users.

        Returns:
            Die Note falls sie existiert und requesting_user_id = owner,
            sonst None.
        """
        note = self._notes.get(note_id)
        if note is None:
            return None
        # KRITISCH: Filterung auf UserId — kein User kann andere Users' Daten sehen
        if note.user_id != requesting_user_id:
            return None
        return note

    def list_by_user(self, user_id: UUID) -> list[DummyNote]:
        """Auflisten aller Notes für einen User.

        KRITISCH: Filtert auf UserId — nur Notes des Users werden
        zurückgegeben.

        Args:
            user_id: Die UUID des Users.

        Returns:
            Liste aller Notes, die diesem User gehören.
        """
        return [note for note in self._notes.values() if note.user_id == user_id]

    def update(
        self,
        note_id: UUID,
        requesting_user_id: UUID,
        if_match: RowVersion | None,
        title: str,
        content: str,
    ) -> DummyNote:
        """Aktualisiere eine Note mit Optimistic-Concurrency-Control.

        KRITISCH: Implementiert If-Match-Validierung (Concurrency-Check):
        - Ist if_match=None: 409 (Client muss aktuelle Version mitliefern)
        - Ist if_match != aktuelle RowVersion: 409 (veraltet)
        - Stimmt if_match überein: Update erfolgreich, neue RowVersion

        Args:
            note_id: Die ID der zu aktualisierenden Note.
            requesting_user_id: Die UUID des anfragenden Users.
            if_match: Erwartet vom Client die aktuelle RowVersion.
            title: Neuer Titel.
            content: Neuer Inhalt.

        Returns:
            Die aktualisierte DummyNote mit neuer RowVersion.

        Raises:
            ConcurrencyConflictError: Wenn if_match fehlt oder veraltet ist.
            ValueError: Wenn die Note nicht existiert oder nicht zum User gehört.
        """
        note = self._notes.get(note_id)
        if note is None:
            msg = f"Note {note_id} not found"
            raise ValueError(msg)
        # User-Isolation: nur der Owner kann aktualisieren
        if note.user_id != requesting_user_id:
            msg = f"User {requesting_user_id} does not own note {note_id}"
            raise ValueError(msg)

        # KRITISCH: Optimistic-Concurrency-Check
        if if_match is None:
            # Kein If-Match gesetzt → 409 mit aktuellem Server-Stand
            msg = "If-Match header required for update"
            raise ConcurrencyConflictError(
                msg,
                current_version=note.row_version,
                instance=f"/notes/{note_id}",
            )
        if if_match.xmin != note.row_version.xmin:
            # If-Match stimmt nicht überein → 409
            msg = f"If-Match mismatch: expected {note.row_version.xmin}, got {if_match.xmin}"
            raise ConcurrencyConflictError(
                msg,
                current_version=note.row_version,
                instance=f"/notes/{note_id}",
            )

        # Update erfolgreich — inkrementiere xmin (neue RowVersion)
        new_row_version = RowVersion.from_xmin(self._xmin_counter)
        self._xmin_counter += 1
        updated_note = DummyNote(
            id=note_id,
            user_id=note.user_id,
            title=title,
            content=content,
            row_version=new_row_version,
        )
        self._notes[note_id] = updated_note
        return updated_note


# ============================================================================
# Acceptance Criteria Tests
# ============================================================================


class TestUserIsolationViaIUserOwned:
    """AC1: Ein Test-Repository nutzt IUserOwned und filtern auf UserId."""

    def test_get_by_id_returns_none_for_other_user(self) -> None:
        """Verschiedene Users können jeweils nur ihre eigenen Notes sehen."""
        repo = InMemoryDummyNoteRepository()
        user_a = uuid4()
        user_b = uuid4()

        # User A erstellt eine Note
        note_a = repo.create(user_a, "User A's Note", "Content A")

        # User B kann die Note von User A NICHT sehen (Isolation)
        retrieved = repo.get_by_id(note_a.id, user_b)
        assert retrieved is None

        # Aber User A kann seine eigene Note sehen
        retrieved = repo.get_by_id(note_a.id, user_a)
        assert retrieved is not None
        assert retrieved.id == note_a.id

    def test_list_by_user_shows_only_own_notes(self) -> None:
        """list_by_user gibt nur Notes des Users zurück."""
        repo = InMemoryDummyNoteRepository()
        user_a = uuid4()
        user_b = uuid4()

        # User A erstellt 2 Notes
        repo.create(user_a, "Note 1", "Content 1")
        repo.create(user_a, "Note 2", "Content 2")

        # User B erstellt 1 Note
        repo.create(user_b, "Note B", "Content B")

        # User A sieht nur seine 2 Notes
        notes_a = repo.list_by_user(user_a)
        assert len(notes_a) == 2
        assert all(n.user_id == user_a for n in notes_a)

        # User B sieht nur seine 1 Note
        notes_b = repo.list_by_user(user_b)
        assert len(notes_b) == 1
        assert notes_b[0].user_id == user_b


class TestUUIDv7Monotonicity:
    """AC2: uuid7() erzeugt zeitsortierte, monoton aufsteigende UUIDs."""

    def test_uuid7_is_monotonically_increasing(self) -> None:
        """Aufeinanderfolgende uuid7()-Aufrufe sind streng monoton aufsteigend."""
        # Generiere mindestens 3 aufeinanderfolgende UUIDs
        uuids = [uuid7() for _ in range(5)]

        # Alle UUIDs sind verschieden
        assert len(uuids) == len(set(uuids))

        # Alle UUIDs sortieren aufsteigend (Monotonie)
        sorted_uuids = sorted(uuids)
        assert uuids == sorted_uuids

    def test_uuid7_version_and_variant(self) -> None:
        """uuid7() erzeugt gültige Version-7-UUIDs (RFC 9562)."""
        u = uuid7()

        # UUID muss gültig sein
        assert isinstance(u, UUID)

        # Version ist 7
        assert u.version == 7

        # Variant ist RFC4122 (standard UUID variant)
        assert u.variant == "specified in RFC 4122"


class TestOptimisticConcurrencyControl:
    """AC3: Update ohne/mit veraltetem If-Match → 409 Concurrency-Conflict."""

    def test_update_without_if_match_raises_409(self) -> None:
        """Update ohne If-Match liefert 409 mit aktuellem Serverstand."""
        repo = InMemoryDummyNoteRepository()
        user = uuid4()
        note = repo.create(user, "Original Title", "Original Content")

        # Versuche Update ohne If-Match → sollte 409 werfen
        with pytest.raises(ConcurrencyConflictError) as exc_info:
            repo.update(
                note.id,
                user,
                if_match=None,  # Kein If-Match
                title="New Title",
                content="New Content",
            )

        # Exception enthält aktuelle Server-RowVersion
        error = exc_info.value
        assert error.http_status == 409
        assert error.current_version.xmin == note.row_version.xmin

    def test_update_with_stale_if_match_raises_409(self) -> None:
        """Update mit veralteter If-Match liefert 409."""
        repo = InMemoryDummyNoteRepository()
        user = uuid4()
        note = repo.create(user, "Original Title", "Original Content")

        # Simuliere: ein anderer Request aktualisiert erst die Note
        updated_note = repo.update(
            note.id,
            user,
            if_match=note.row_version,  # Mit aktuellem If-Match
            title="Intermediate Update",
            content="Intermediate Content",
        )
        # Nun hat updated_note eine neue (höhere) RowVersion

        # Versuche Update mit der ALTEN RowVersion → sollte 409 werfen
        with pytest.raises(ConcurrencyConflictError) as exc_info:
            repo.update(
                note.id,
                user,
                if_match=note.row_version,  # Alte (stale) RowVersion
                title="New Title",
                content="New Content",
            )

        # Exception enthält die aktuelle (neue) Server-RowVersion
        error = exc_info.value
        assert error.http_status == 409
        assert error.current_version.xmin == updated_note.row_version.xmin
        assert error.current_version.xmin > note.row_version.xmin

    def test_update_with_correct_if_match_succeeds(self) -> None:
        """Update mit korrektem If-Match erfolgreich, neue RowVersion."""
        repo = InMemoryDummyNoteRepository()
        user = uuid4()
        note = repo.create(user, "Original Title", "Original Content")
        old_version = note.row_version.xmin

        # Update mit aktuellem If-Match sollte erfolgreich sein
        updated = repo.update(
            note.id,
            user,
            if_match=note.row_version,
            title="New Title",
            content="New Content",
        )

        # Update war erfolgreich
        assert updated.title == "New Title"
        assert updated.content == "New Content"

        # RowVersion wurde inkrementiert
        assert updated.row_version.xmin > old_version

    def test_update_respects_user_isolation(self) -> None:
        """User B kann Notes von User A nicht aktualisieren (kein Ownership)."""
        repo = InMemoryDummyNoteRepository()
        user_a = uuid4()
        user_b = uuid4()

        note_a = repo.create(user_a, "User A's Note", "Content A")

        # User B versucht die Note von User A zu aktualisieren
        with pytest.raises(ValueError, match="does not own"):
            repo.update(
                note_a.id,
                user_b,  # User B versucht zu aktualisieren
                if_match=note_a.row_version,
                title="Hacked",
                content="Hacked",
            )

        # Die Note von User A ist unverändert
        note_unchanged = repo.get_by_id(note_a.id, user_a)
        assert note_unchanged is not None
        assert note_unchanged.title == "User A's Note"


class TestRowVersionParsing:
    """Tests für RowVersion.from_if_match und Serialisierung."""

    def test_row_version_from_xmin(self) -> None:
        """RowVersion lässt sich aus xmin erstellen."""
        rv = RowVersion.from_xmin(12345)
        assert rv.xmin == 12345

    def test_row_version_rejects_negative_xmin(self) -> None:
        """RowVersion lehnt negative xmin ab."""
        with pytest.raises(ValueError, match="non-negative"):
            RowVersion.from_xmin(-1)

    def test_row_version_from_if_match_success(self) -> None:
        """from_if_match parsed gültigen If-Match-Header."""
        result = RowVersion.from_if_match("12345")
        assert result is not None
        match result:
            case Ok(rv):
                assert rv.xmin == 12345
            case Err(_):
                pytest.fail("Expected Ok result")

    def test_row_version_from_if_match_none(self) -> None:
        """from_if_match gibt None für None-Header zurück."""
        result = RowVersion.from_if_match(None)
        assert result is None

    def test_row_version_from_if_match_invalid(self) -> None:
        """from_if_match lehnt nicht-numerische Header ab."""
        result = RowVersion.from_if_match("not-a-number")
        assert result is not None
        match result:
            case Err(msg):
                assert "Invalid If-Match" in msg
            case Ok(_):
                pytest.fail("Expected Err result")

    def test_row_version_str(self) -> None:
        """RowVersion lässt sich zu String für Header serialisieren."""
        rv = RowVersion.from_xmin(99999)
        assert str(rv) == "99999"
