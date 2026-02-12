from unittest.mock import patch, MagicMock
from app.tools.sound_tools import (
    SOUND_TAGS,
    play_sound_by_name,
    play_random_sound,
    dog_bark,
    doorbell,
    coughing_fit,
    _play_sound,
)


class TestSoundTags:
    def test_contains_dog_bark(self):
        assert "DOG_BARK" in SOUND_TAGS

    def test_contains_doorbell(self):
        assert "DOORBELL" in SOUND_TAGS

    def test_contains_coughing_fit(self):
        assert "COUGHING_FIT" in SOUND_TAGS

    def test_maps_to_mp3_files(self):
        for tag, filename in SOUND_TAGS.items():
            assert filename.endswith(".mp3"), f"{tag} should map to an mp3 file"


class TestPlaySoundByName:
    @patch("app.tools.sound_tools._play_sound")
    def test_valid_tag_calls_play_sound(self, mock_play):
        play_sound_by_name("DOG_BARK")
        mock_play.assert_called_once_with("dog-barking.mp3")

    @patch("app.tools.sound_tools._play_sound")
    def test_doorbell_tag(self, mock_play):
        play_sound_by_name("DOORBELL")
        mock_play.assert_called_once_with("doorbell.mp3")

    @patch("app.tools.sound_tools._play_sound")
    def test_invalid_tag_does_not_crash(self, mock_play):
        play_sound_by_name("NONEXISTENT")
        mock_play.assert_not_called()


class TestPlayRandomSound:
    @patch("app.tools.sound_tools._play_sound")
    def test_calls_a_sound_function(self, mock_play):
        play_random_sound()
        # One of the internal sound functions should have been called,
        # which in turn calls _play_sound
        mock_play.assert_called_once()


class TestToolFunctions:
    @patch("app.tools.sound_tools._play_sound")
    def test_dog_bark_returns_sound_effect(self, mock_play):
        result = dog_bark.invoke({})
        assert "DOG_BARKING" in result

    @patch("app.tools.sound_tools._play_sound")
    def test_doorbell_returns_sound_effect(self, mock_play):
        result = doorbell.invoke({})
        assert "DOORBELL" in result

    @patch("app.tools.sound_tools._play_sound")
    def test_coughing_fit_returns_sound_effect(self, mock_play):
        result = coughing_fit.invoke({})
        assert "COUGHING_FIT" in result


class TestPlaySoundErrorHandling:
    def test_missing_file_does_not_crash(self, mock_pygame):
        """_play_sound handles missing files gracefully."""
        mock_pygame.music.load.side_effect = Exception("File not found")
        # Should not raise
        _play_sound("nonexistent.mp3")
