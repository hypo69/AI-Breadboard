import pytest
from unittest.mock import Mock, patch, mock_open
from src.utils.ftp import write, read, delete

class TestFtp_HappyPath:
    """Testing normal expected scenarios of FTP module operation.
    """

    @patch('src.utils.ftp.ftplib.FTP')
    def test_write_success(self, mock_ftp):
        """Test write function with correct data.
        """
        mock_session = mock_ftp.return_value
        with patch('builtins.open', mock_open()):
            result = write('test.txt', '/remote', 'test.txt')
            assert result is True
            mock_session.cwd.assert_called_with('/remote')
            mock_session.storbinary.assert_called()

    @patch('src.utils.ftp.ftplib.FTP')
    def test_read_success(self, mock_ftp):
        """Test read function with correct data.
        """
        mock_session = mock_ftp.return_value
        with patch('builtins.open') as mock_file:
            result = read('test.txt', '/remote', 'test.txt')
            assert result is not None
            mock_session.cwd.assert_called_with('/remote')
            mock_session.retrbinary.assert_called()

    @patch('src.utils.ftp.ftplib.FTP')
    def test_delete_success(self, mock_ftp):
        """Test delete function with correct data.
        """
        mock_session = mock_ftp.return_value
        result = delete('test.txt', '/remote', 'test.txt')
        assert result is True
        mock_session.cwd.assert_called_with('/remote')
        mock_session.delete.assert_called_with('test.txt')