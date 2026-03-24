from unittest.mock import patch

from pyssg.commands.init import InitCommand

TEST_PATH = "pyssg.commands.init"


class TestCreateFolder:
    @patch(f"{TEST_PATH}.Path")
    @patch(f"{TEST_PATH}.os")
    def test_creates_folder_when_none_exists(self, mock_os, mock_path, tmp_path):
        mock_path.cwd.return_value = tmp_path
        command = InitCommand(folder_name="test_folder")
        mock_os.path.exists.return_value = False

        with patch.object(command, "_info") as mock_info:
            result = command._create_folder()

        assert result is True
        mock_info.assert_called_once_with("Created folder: test_folder")
        mock_os.mkdir.assert_called_once_with(tmp_path / "test_folder")

    @patch(f"{TEST_PATH}.Path")
    @patch(f"{TEST_PATH}.os")
    def test_doesnt_create_folder_when_exists(self, mock_os, mock_path, tmp_path):
        mock_path.cwd.return_value = tmp_path
        command = InitCommand(folder_name="test_folder")
        mock_os.path.exists.return_value = True

        with patch.object(command, "_warning") as mock_warning:
            result = command._create_folder()

        assert result is False
        mock_warning.assert_called_once_with("Folder already exists: test_folder")
        mock_os.mkdir.assert_not_called()


class TestInitStructure:
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.Path")
    @patch(f"{TEST_PATH}.files")
    @patch(f"{TEST_PATH}.shutil")
    @patch(f"{TEST_PATH}.os")
    def test_creates_folders_and_files(
        self, mock_os, mock_shutil, mock_files, mock_path, mock_cache_cls, tmp_path
    ):
        command = InitCommand(folder_name=".")
        mock_os.path.isfile.return_value = False
        traversable = mock_files("pyssg") / "templates" / "py-ssg.toml"
        expected_src = mock_path(str(traversable))

        with patch.object(command, "_success") as mock_success:
            command._init_structure(folder=tmp_path)

        mock_os.path.isfile.assert_called_once_with(tmp_path / "py-ssg.toml")
        mock_os.mkdir.assert_any_call(tmp_path / "content")
        mock_os.mkdir.assert_any_call(tmp_path / "templates")
        mock_os.mkdir.assert_any_call(tmp_path / "components")
        mock_os.mkdir.assert_any_call(tmp_path / "output")
        assert mock_os.mkdir.call_count == 4
        mock_shutil.copy2.assert_called_once_with(
            expected_src, tmp_path / "py-ssg.toml"
        )
        mock_success.assert_called_once_with(f"Initialized structure in: {tmp_path}")

    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.Path")
    @patch(f"{TEST_PATH}.files")
    @patch(f"{TEST_PATH}.shutil")
    @patch(f"{TEST_PATH}.os")
    def test_creates_cache_file(
        self, mock_os, mock_shutil, mock_files, mock_path, mock_cache_cls, tmp_path
    ):
        command = InitCommand(folder_name=".")
        mock_os.path.isfile.return_value = False

        with patch.object(command, "_success"):
            command._init_structure(folder=tmp_path)

        mock_cache_cls.create.assert_called_once_with(cache_dir=tmp_path)

    @patch(f"{TEST_PATH}.os")
    def test_errors_when_config_exists(self, mock_os, tmp_path):
        command = InitCommand(folder_name=".")
        mock_os.path.isfile.return_value = True

        with patch.object(command, "_error") as mock_error:
            command._init_structure(folder=tmp_path)

        mock_error.assert_called_once_with("Configuration files already exist!")
        mock_os.mkdir.assert_not_called()


class TestExecute:
    @patch(f"{TEST_PATH}.Path")
    @patch.object(InitCommand, "_init_structure")
    @patch.object(InitCommand, "_create_folder")
    def test_inits_in_current_folder(
        self, mock_create_folder, mock_init_structure, mock_path, tmp_path
    ):
        mock_path.cwd.return_value = tmp_path
        command = InitCommand(folder_name=".")

        with patch.object(command, "_info"):
            command.execute()

        mock_create_folder.assert_not_called()
        mock_init_structure.assert_called_once_with(folder=tmp_path)

    @patch(f"{TEST_PATH}.Path")
    @patch.object(InitCommand, "_init_structure")
    @patch.object(InitCommand, "_create_folder")
    def test_inits_in_new_folder(
        self, mock_create_folder, mock_init_structure, mock_path, tmp_path
    ):
        mock_path.cwd.return_value = tmp_path
        mock_create_folder.return_value = True
        command = InitCommand(folder_name="new_folder")

        with patch.object(command, "_info"):
            command.execute()

        mock_create_folder.assert_called_once_with()
        mock_init_structure.assert_called_once_with(folder=tmp_path / "new_folder")

    @patch(f"{TEST_PATH}.Path")
    @patch.object(InitCommand, "_init_structure")
    @patch.object(InitCommand, "_create_folder")
    def test_aborts_when_folder_already_exists(
        self, mock_create_folder, mock_init_structure, mock_path, tmp_path
    ):
        mock_path.cwd.return_value = tmp_path
        mock_create_folder.return_value = False
        command = InitCommand(folder_name="existing_folder")

        command.execute()

        mock_init_structure.assert_not_called()
