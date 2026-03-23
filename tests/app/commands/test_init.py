from unittest.mock import patch

from pyssg.modules.commands.init import InitCommand

TEST_PATH = "pyssg.modules.commands.init"


class TestInitCommand:
    @patch(f"{TEST_PATH}.Path")
    @patch(f"{TEST_PATH}.logger")
    @patch(f"{TEST_PATH}.os")
    def test_creates_folder_when_none_exists(
        self,
        mock_os,
        mock_logger,
        mock_path,
        tmp_path,
    ):
        mock_path.cwd.return_value = tmp_path
        command = InitCommand(folder_name="test_folder")
        mock_os.path.exists.return_value = False

        command._create_folder()

        mock_logger.info.assert_called_once_with("Created folder: test_folder")
        mock_logger.warning.assert_not_called()
        mock_os.mkdir.assert_called_once_with(tmp_path / "test_folder")

    @patch(f"{TEST_PATH}.Path")
    @patch(f"{TEST_PATH}.logger")
    @patch(f"{TEST_PATH}.os")
    def test_doesnt_create_folder_when_exists(
        self,
        mock_os,
        mock_logger,
        mock_path,
        tmp_path,
    ):
        mock_path.cwd.return_value = tmp_path
        command = InitCommand(folder_name="test_folder")
        mock_os.path.exists.return_value = True

        command._create_folder()

        mock_logger.info.assert_not_called()
        mock_logger.warning.assert_called_once_with(
            "Folder already exists: test_folder",
        )
        mock_os.mkdir.assert_not_called()

    @patch(f"{TEST_PATH}.Path")
    @patch.object(InitCommand, "_init_structure")
    @patch.object(InitCommand, "_create_folder")
    def test_execute_inits_in_current_folder(
        self,
        mock_create_folder,
        mock_init_structure,
        mock_path,
        tmp_path,
    ):
        mock_path.cwd.return_value = tmp_path
        command = InitCommand(folder_name=".")

        command.execute()

        mock_create_folder.assert_not_called()
        mock_init_structure.assert_called_once_with(folder=tmp_path)

    @patch(f"{TEST_PATH}.Path")
    @patch.object(InitCommand, "_init_structure")
    @patch.object(InitCommand, "_create_folder")
    def test_execute_inits_in_new_folder(
        self,
        mock_create_folder,
        mock_init_structure,
        mock_path,
        tmp_path,
    ):
        mock_path.cwd.return_value = tmp_path
        command = InitCommand(folder_name="new_folder")

        command.execute()

        mock_create_folder.assert_called_once_with()
        mock_init_structure.assert_called_once_with(folder=tmp_path / "new_folder")

    @patch(f"{TEST_PATH}.Path")
    @patch(f"{TEST_PATH}.files")
    @patch(f"{TEST_PATH}.logger")
    @patch(f"{TEST_PATH}.shutil")
    @patch(f"{TEST_PATH}.os")
    def test_init_structure_creates_folders_and_files(
        self,
        mock_os,
        mock_shutil,
        mock_logger,
        mock_files,
        mock_path,
        tmp_path,
    ):
        command = InitCommand(folder_name=".")
        mock_os.path.isfile.return_value = False
        traversable = mock_files("pyssg") / "templates" / "py-ssg.toml"
        expected_src = mock_path(str(traversable))

        command._init_structure(folder=tmp_path)

        mock_os.path.isfile.assert_called_once_with(tmp_path / "py-ssg.toml")
        mock_os.mkdir.assert_any_call(tmp_path / "content")
        mock_os.mkdir.assert_any_call(tmp_path / "templates")
        mock_os.mkdir.assert_any_call(tmp_path / "output")
        assert mock_os.mkdir.call_count == 3
        mock_shutil.copy2.assert_called_once_with(
            expected_src,
            tmp_path / "py-ssg.toml",
        )
        mock_logger.warning.assert_not_called()
        mock_logger.info.assert_called_once_with(
            f"Initialized structure in: {tmp_path}",
        )

    @patch(f"{TEST_PATH}.logger")
    @patch(f"{TEST_PATH}.os")
    def test_init_structure_warns_when_config_exists(
        self,
        mock_os,
        mock_logger,
        tmp_path,
    ):
        command = InitCommand(folder_name=".")
        mock_os.path.isfile.return_value = True

        command._init_structure(folder=tmp_path)

        mock_logger.warning.assert_called_once_with(
            "Config file already exists: py-ssg.toml",
        )
        mock_os.mkdir.assert_not_called()
