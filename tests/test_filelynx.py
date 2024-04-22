import os
from pathlib import Path
from datetime import date, datetime

import pytest

from app.filelynx import FileLynx


@pytest.fixture()
def temp_file_dir(tmp_path):
    _make_dummy_file(tmp_path, 'aac', 'txt', 4123)
    _make_dummy_file(tmp_path, 'abc', 'txt', 6123)
    _make_dummy_file(tmp_path, 'klm', 'txt', 23)

    _make_dummy_file(tmp_path, 'image1', 'jpg', 2884)
    _make_dummy_file(tmp_path, 'some-img', 'jpg', 300)
    _make_dummy_file(tmp_path, 'another', 'jpg', 4123)

    _make_dummy_file(tmp_path, 'docu', 'pdf', 1000)
    _make_dummy_file(tmp_path, 'invoice', 'pdf', 23)
    _make_dummy_file(tmp_path, 'docu2', 'pdf', 23705)

    _make_dummy_folder(tmp_path, 'sub')
    _make_dummy_folder(tmp_path, 'Downloads')
    _make_dummy_folder(tmp_path, 'Books')
    yield tmp_path


@pytest.fixture()
def temp_dir_meta():
    """
    Returns:
        A list of tuples with the following indices
            0 - name,
            1 - extension,
            2 - size,
            3 - type
    """
    yield [
        ('aac', 'txt', 4123, 'file'),
        ('abc', 'txt', 6123, 'file'),
        ('klm', 'txt', 23, 'file'),
        ('image1', 'jpg', 2884, 'file'),
        ('some-img', 'jpg', 300, 'file'),
        ('another', 'jpg', 4123, 'file'),
        ('docu', 'pdf', 1000, 'file'),
        ('invoice', 'pdf', 23, 'file'),
        ('docu2', 'pdf', 23705, 'file'),
        ('sub', '', 0, 'folder'),
        ('Downloads', '', 0, 'folder'),
        ('Books', '', 0, 'folder'),
    ]


class TestFileLynxInit:

    @pytest.fixture()
    def file_path(self, tmp_path):
        filename = 'abcdefg'
        ext = 'txt'
        _make_dummy_file(tmp_path, filename, ext, 5)
        file_path = tmp_path / f'{filename}.{ext}'
        yield file_path

    @pytest.mark.parametrize('nonexistent_path',
                             ['./fjieoajiidoihg', 'aefae8s', './oapd/fiswre', Path('./argaerh'), Path('nslgn')])
    def test_constructor_should_raise_when_path_not_exists(self, nonexistent_path, temp_file_dir):
        # given
        sut = FileLynx(temp_file_dir)

        # when
        with pytest.raises(ValueError) as exc_info:
            sut.set_dir(nonexistent_path)

        # then
        assert '[new_dir] argument is not an existing path' in exc_info.value.args[0]

    def test_constructor_should_raise_when_path_is_not_dir(self, temp_file_dir, file_path):
        # given
        sut = FileLynx(temp_file_dir)

        # when
        with pytest.raises(ValueError) as exc_info:
            sut.set_dir(file_path)

        # then
        assert '[new_dir] argument is not a directory' in exc_info.value.args[0]


class TestFileLynxLs:

    @pytest.mark.parametrize('type_filter', [['sth'], ['sth', 'abc'], ['file', 'aabb']])
    def test_ls_should_raise_when_type_filter_is_wrong(self, type_filter, temp_file_dir):
        # given
        sut = FileLynx(temp_file_dir)

        # when
        with pytest.raises(ValueError) as exc_info:
            actual = sut.ls(type_filter=type_filter)

        # then
        assert '[type_filter] parameter contains invalid items. Must be one of: "file", "folder"' in \
               exc_info.value.args[0]

    @pytest.mark.parametrize('sort_by', ['hello', 'abc'])
    def test_ls_should_raise_when_sort_by_is_wrong(self, sort_by, temp_file_dir):
        # given
        sut = FileLynx(temp_file_dir)

        # when
        with pytest.raises(ValueError) as exc_info:
            actual = sut.ls(sort_by=sort_by)

        # then
        assert f'"{sort_by}" is not a valid sorting key. Must be one of: "name", "datetime", "size"' in \
               exc_info.value.args[0]

    def test_ls_should_return_default_order_when_no_params_given(self, temp_file_dir, temp_dir_meta):
        # given
        sut = FileLynx(temp_file_dir)
        expected_len = len(temp_dir_meta)
        expected_name_order = sorted([m[0] for m in temp_dir_meta],
                                     key=lambda f: f.lower())

        # when
        actual = sut.ls()

        # then
        assert isinstance(actual, list)
        assert len(actual) == expected_len
        for expected, elem in zip(expected_name_order, actual):
            assert expected == elem.stem

    @pytest.mark.parametrize("folder_filter", [['folder'], ['Folder'], ['foLDeR']])
    def test_ls_should_return_only_folders_when_type_filter_is_folder(self, temp_file_dir, temp_dir_meta,
                                                                      folder_filter):
        # given
        sut = FileLynx(temp_file_dir)
        expected = [m[0] for m in temp_dir_meta if m[3] == 'folder']

        # when
        actual = sut.ls(type_filter=folder_filter)

        # then
        names = set(map(lambda f: f.stem, actual))
        assert len(expected) == len(actual)
        assert set(expected).issubset(names)
        assert names.issubset(set(expected))
        for elem in actual:
            assert elem.is_dir()

    @pytest.mark.parametrize("file_filter", [['file'], ['File'], ['fILE']])
    def test_ls_should_return_only_files_when_type_filter_is_file(self, temp_file_dir, temp_dir_meta, file_filter):
        # given
        sut = FileLynx(temp_file_dir)
        expected = [m[0] for m in temp_dir_meta if m[3] == 'file']

        # when
        actual = sut.ls(type_filter=file_filter)

        # then
        names = set(map(lambda f: f.stem, actual))
        assert len(expected) == len(actual)
        assert set(expected).issubset(names)
        assert names.issubset(set(expected))
        for elem in actual:
            assert elem.is_file()

    @pytest.mark.parametrize("type_filter", [['file', 'folder'], ['File', 'Folder'], ['fILE', 'fOLdER']])
    def test_ls_should_return_all_when_type_filter_is_all(self, temp_file_dir, temp_dir_meta, type_filter):
        # given
        sut = FileLynx(temp_file_dir)
        expected = [m[0] for m in temp_dir_meta]

        # when
        actual = sut.ls(type_filter=type_filter)

        # then
        names = set(map(lambda f: f.stem, actual))
        assert len(expected) == len(actual)
        assert set(expected).issubset(names)
        assert names.issubset(set(expected))

    @pytest.mark.parametrize('extension_filter', [['txT'], ['jpg', 'pDF', 'sthelse'], ['txt', 'Jpg', 'PDF', '']])
    def test_ls_should_return_only_specified_extensions(self, temp_file_dir, temp_dir_meta, extension_filter):
        # given
        sut = FileLynx(temp_file_dir)
        expected_extensions = [e.lower() for e in extension_filter]
        expected_len = len([m for m in temp_dir_meta if m[1] in expected_extensions and m[3] != 'folder'])

        # when
        actual = sut.ls(extension_filter=extension_filter)

        # then
        for elem in actual:
            assert elem.is_file()
            assert elem.suffix[1:] in expected_extensions
        assert len(actual) == expected_len

    @pytest.mark.parametrize("sort_by_name,ascending", [('nAMe', True), ('name', False)])
    def test_ls_should_return_sorted_by_name_when_sort_by_name(self, sort_by_name, ascending,
                                                               temp_file_dir, temp_dir_meta):
        # given
        sut = FileLynx(temp_file_dir)
        expected = sorted([m[0] for m in temp_dir_meta],
                          key=lambda name: name.lower(), reverse=not ascending)

        # when
        actual = sut.ls(sort_by=sort_by_name, ascending=ascending)

        # then
        assert len(expected) == len(actual)
        for e, a in zip(expected, actual):
            assert e == a.stem

    @pytest.mark.parametrize("sort_by_size,ascending", [('siZe', True), ('size', False)])
    def test_ls_should_return_sorted_by_size_when_sort_by_size(self, sort_by_size, ascending,
                                                               temp_file_dir, temp_dir_meta):
        # given
        sut = FileLynx(temp_file_dir)
        expected = sorted(temp_dir_meta, key=lambda elem: elem[2], reverse=not ascending)

        # when
        actual = sut.ls(sort_by=sort_by_size, ascending=ascending)

        # then
        assert len(expected) == len(actual)
        for e, a in zip(expected, actual):
            assert e[2] == a.stat().st_size

    @pytest.mark.parametrize("sort_by_datetime,ascending", [('datetIMe', True), ('datetime', False)])
    def test_ls_should_return_sorted_by_datetime_when_sort_by_datetime(self, sort_by_datetime, ascending,
                                                                       temp_file_dir, temp_dir_meta):
        # given
        sut = FileLynx(temp_file_dir)

        # when
        output = sut.ls(sort_by=sort_by_datetime, ascending=ascending)

        # then
        for i in range(len(output) - 1):
            if ascending:
                assert output[i].stat().st_mtime <= output[i + 1].stat().st_mtime
            else:
                assert output[i].stat().st_mtime >= output[i + 1].stat().st_mtime


class TestFileLynxSubgroup:

    @pytest.mark.parametrize('by', ['aeg', 'WRONG', 'nothing'])
    def test_subgroup_should_raise_when_by_is_wrong(self, by, temp_file_dir):
        # given
        sut = FileLynx(temp_file_dir)

        # when
        with pytest.raises(ValueError) as exc_info:
            sut.subgroup(by)

        # then
        assert '[by] parameter contains an invalid subgrouping condition' in exc_info.value.args[0]

    @pytest.mark.parametrize('by_ext', ['ext', 'EXT', 'exT'])
    def test_subgroup_should_group_by_extension_when_by_is_ext(self, by_ext, temp_file_dir, temp_dir_meta):
        # given
        sut = FileLynx(temp_file_dir)
        expected_contents = ([m[1] for m in temp_dir_meta if m[3] == 'file'] +
                             [m[0] for m in temp_dir_meta if m[3] == 'folder'])
        expected_num = len(set(m[1] for m in temp_dir_meta if m[3] == 'file'))

        # when
        actual_num = sut.subgroup(by_ext)

        # then
        assert expected_num == actual_num
        children = list(temp_file_dir.iterdir())
        children_names = [child.stem for child in children]
        assert set(children_names).issubset(set(expected_contents))
        assert set(expected_contents).issubset(set(children_names))
        for child in children:
            assert child.is_dir()

    def test_subgroup_should_name_folders_correctly_when_map_given(self, temp_file_dir, temp_dir_meta):
        # given
        ext_to_name_map = {'tXT': 'Texts', 'jPg': 'Images', 'dummyext': 'somename'}
        sut = FileLynx(temp_file_dir)
        expected_folder_names = {'Texts', 'Images', 'pdf', 'sub', 'Downloads', 'Books'}
        expected_num = len(set(m[1] for m in temp_dir_meta if m[3] == 'file'))

        # when
        actual_num = sut.subgroup('ext', ext_to_name_map=ext_to_name_map)

        # then
        assert expected_num == actual_num
        contents = set(child.name for child in temp_file_dir.iterdir())
        assert expected_folder_names.issubset(contents)
        assert contents.issubset(expected_folder_names)

    @pytest.mark.parametrize('by_date', ['date', 'DATE', 'DAte'])
    def test_subgroup_should_group_by_date_when_by_is_date(self, by_date, temp_file_dir, temp_dir_meta):
        # given
        sut = FileLynx(temp_file_dir)
        new_folder_name = date.today().strftime('%d-%m-%Y')
        expected_folder_names = set(c[0] for c in temp_dir_meta if c[3] == 'folder')
        expected_folder_names.add(new_folder_name)
        expected_num = 1

        # when
        actual_num = sut.subgroup(by_date)

        # then
        assert expected_num == actual_num
        actual_names = set(child.name for child in temp_file_dir.iterdir() if child.is_dir())
        assert expected_folder_names.issubset(actual_names)
        assert actual_names.issubset(expected_folder_names)

    @pytest.mark.parametrize('dt_format', ['%m.%d.%y', '%d_%b_%Y', '%Y-%B-%d'])
    def test_subgroup_should_format_folder_name_when_dt_format_is_given(self, dt_format, temp_file_dir, temp_dir_meta):
        # given
        sut = FileLynx(temp_file_dir)
        new_folder_name = date.today().strftime(dt_format)
        expected_folder_names = set(c[0] for c in temp_dir_meta if c[3] == 'folder')
        expected_folder_names.add(new_folder_name)
        expected_num = 1

        # when
        actual_num = sut.subgroup('date', dt_format=dt_format)

        # then
        assert expected_num == actual_num
        actual_names = set(child.name for child in temp_file_dir.iterdir() if child.is_dir())
        assert expected_folder_names.issubset(actual_names)
        assert actual_names.issubset(expected_folder_names)


class TestFileLynxBatchRename:

    def test_batch_rename_should_raise_when_before_earlier_than_after(self, temp_file_dir):
        # given
        sut = FileLynx(temp_file_dir)
        before = datetime(2022, 10, 5, 15, 29)
        after = datetime(2022, 11, 17, 14, 52)

        # when
        with pytest.raises(ValueError) as exc_info:
            sut.batch_rename('somename', before=before, after=after)

        # then
        assert '[before] argument can\'t be less than [after]' in exc_info.value.args[0]

    @pytest.mark.parametrize('sort_by', ['invalid', 'aaBb'])
    def test_batch_rename_should_raise_when_sort_by_is_wrong(self, sort_by, temp_file_dir):
        # given
        sut = FileLynx(temp_file_dir)

        # when
        with pytest.raises(ValueError) as exc_info:
            sut.batch_rename('something', sort_by=sort_by)

        # then
        assert '[sort_by] argument contains an invalid sorting key' in exc_info.value.args[0]

    def test_batch_rename_should_raise_when_numerator_start_is_below_zero(self, temp_file_dir):
        # given
        sut = FileLynx(temp_file_dir)
        numerator_start = -1

        # when
        with pytest.raises(ValueError) as exc_info:
            sut.batch_rename('something', numerator_start=numerator_start)

        # then
        assert '[numerator_start] cannot be below zero' in exc_info.value.args[0]

    def test_batch_rename_should_rename_files(self, temp_file_dir, temp_dir_meta):
        # given
        new_name = 'something'
        size = len([c for c in temp_dir_meta if c[3] == 'file'])
        expected_names = {f'{new_name}_{i}' for i in range(1, size + 1)}
        expected_names.update([c[0] for c in temp_dir_meta if c[3] == 'folder'])
        sut = FileLynx(temp_file_dir)

        # when
        num_renamed = sut.batch_rename(new_name)

        # then
        actual_names = set(child.stem for child in temp_file_dir.iterdir())
        assert expected_names.issubset(actual_names)
        assert actual_names.issubset(expected_names)
        assert num_renamed == size

    @pytest.mark.parametrize('sep', [' - ', '#', 'aa'])
    def test_batch_rename_should_rename_correctly_when_sep_given(self, temp_file_dir, temp_dir_meta, sep):
        # given
        new_name = 'something'
        size = len([c for c in temp_dir_meta if c[3] == 'file'])
        expected_names = {f'{new_name}{sep}{i}' for i in range(1, size + 1)}
        expected_names.update([c[0] for c in temp_dir_meta if c[3] == 'folder'])
        sut = FileLynx(temp_file_dir)

        # when
        num_renamed = sut.batch_rename(new_name, sep=sep)

        # then
        actual_names = set(child.stem for child in temp_file_dir.iterdir())
        assert expected_names.issubset(actual_names)
        assert actual_names.issubset(expected_names)
        assert num_renamed == size

    @pytest.mark.parametrize('n_start', [0, 14])
    def test_batch_rename_should_rename_files_correctly_when_numerator_start_given(self, temp_file_dir,
                                                                                   temp_dir_meta, n_start):
        # given
        new_name = 'something'
        size = len([c for c in temp_dir_meta if c[3] == 'file'])
        expected_names = {f'{new_name}_{i}' for i in range(n_start, n_start + size)}
        expected_names.update([c[0] for c in temp_dir_meta if c[3] == 'folder'])
        sut = FileLynx(temp_file_dir)

        # when
        num_renamed = sut.batch_rename(new_name, numerator_start=n_start)

        # then
        actual_names = set(child.stem for child in temp_file_dir.iterdir())
        assert expected_names.issubset(actual_names)
        assert actual_names.issubset(expected_names)
        assert num_renamed == size

    def test_batch_rename_should_rename_files_correctly_when_numerator_first(self, temp_file_dir, temp_dir_meta):
        # given
        new_name = 'something'
        size = len([c for c in temp_dir_meta if c[3] == 'file'])
        expected_names = {f'{i}_{new_name}' for i in range(1, 1 + size)}
        expected_names.update([c[0] for c in temp_dir_meta if c[3] == 'folder'])
        sut = FileLynx(temp_file_dir)

        # when
        num_renamed = sut.batch_rename(new_name, numerator_first=True)

        # then
        actual_names = set(child.stem for child in temp_file_dir.iterdir())
        assert expected_names.issubset(actual_names)
        assert actual_names.issubset(expected_names)
        assert num_renamed == size

    @pytest.mark.parametrize('pad', [-1, -2])
    def test_batch_rename_should_ignore_padding_if_below_zero(self, temp_file_dir, temp_dir_meta, pad):
        # given
        new_name = 'something'
        size = len([c for c in temp_dir_meta if c[3] == 'file'])
        expected_names = {f'{new_name}_{i}' for i in range(1, 1 + size)}
        expected_names.update([c[0] for c in temp_dir_meta if c[3] == 'folder'])
        sut = FileLynx(temp_file_dir)

        # when
        num_renamed = sut.batch_rename(new_name, zero_pad=pad)

        # then
        actual_names = set(child.stem for child in temp_file_dir.iterdir())
        assert expected_names.issubset(actual_names)
        assert actual_names.issubset(expected_names)
        assert num_renamed == size

    @pytest.mark.parametrize('pad', [0, 1, 2, 6])
    def test_batch_rename_should_zero_pad_if_zero_pad_given(self, temp_file_dir, temp_dir_meta, pad):
        # given
        new_name = 'something'
        size = len([c for c in temp_dir_meta if c[3] == 'file'])
        expected_names = {f'{new_name}_{str(i).zfill(pad)}' for i in range(1, 1 + size)}
        expected_names.update([c[0] for c in temp_dir_meta if c[3] == 'folder'])
        sut = FileLynx(temp_file_dir)

        # when
        num_renamed = sut.batch_rename(new_name, zero_pad=pad)

        # then
        actual_names = set(child.stem for child in temp_file_dir.iterdir())
        assert expected_names.issubset(actual_names)
        assert actual_names.issubset(expected_names)
        assert num_renamed == size

    @pytest.mark.parametrize("ext_filter", [['jPG'], ['tXT', 'pdf'], ['jpg', 'dummyext']])
    def test_batch_rename_should_rename_only_specified_extensions(self, temp_file_dir, temp_dir_meta, ext_filter):
        # given
        new_name = 'something'
        ext_filter_lowercase = [ef.lower() for ef in ext_filter]
        size = len([c for c in temp_dir_meta if c[3] == 'file' and c[1] in ext_filter_lowercase])
        expected_names = {f'{new_name}_{i}' for i in range(1, 1 + size)}
        expected_names.update([c[0] for c in temp_dir_meta if c[3] == 'folder'])
        expected_names.update([c[0] for c in temp_dir_meta if c[1] not in ext_filter_lowercase and c[3] == 'file'])
        sut = FileLynx(temp_file_dir)

        # when
        num_renamed = sut.batch_rename(new_name, extension_filter=ext_filter)

        # then
        actual_names = set(child.stem for child in temp_file_dir.iterdir())
        assert expected_names.issubset(actual_names)
        assert actual_names.issubset(expected_names)
        assert num_renamed == size

    @pytest.mark.parametrize('sort_by,ascending',
                             [('nAMe', False), ('Datetime', True), ('datetime', False), ('siZE', False)])
    def test_batch_rename_should_rename_in_correct_order_when_sort_by_given(self, temp_file_dir, temp_dir_meta,
                                                                            sort_by, ascending):
        # given
        new_name = 'something'
        size = len([c for c in temp_dir_meta if c[3] == 'file'])
        sut = FileLynx(temp_file_dir)

        # when
        num_renamed = sut.batch_rename(new_name, sort_by=sort_by, ascending=ascending)

        # then
        assert num_renamed == size
        renamed_files = [c for c in temp_file_dir.iterdir() if c.is_file()]
        renamed_files_sorted = sorted(renamed_files, key=lambda e: e.stem, reverse=not ascending)
        direction = 1 if ascending else -1
        for i in range(0, len(renamed_files_sorted) - 1, direction):
            if sort_by.lower() == 'size':
                assert renamed_files_sorted[i].stat().st_size <= renamed_files_sorted[i + 1].stat().st_size
            elif sort_by.lower() == 'datetime':
                assert renamed_files_sorted[i].stat().st_mtime <= renamed_files_sorted[i + 1].stat().st_mtime


def _make_dummy_file(base_path: Path | str, filename: str, extension: str, size_in_bytes: int):
    if not isinstance(base_path, Path):
        base_path = Path(base_path)
    if not base_path.exists():
        raise RuntimeError(f'path {base_path} doesn\'t exist!')
    if not isinstance(filename, str):
        raise TypeError('[filename] parameter must be a str object.')
    if not isinstance(extension, str):
        raise TypeError('[extension] parameter must be a str object.')

    random_bytes = bytearray(os.urandom(size_in_bytes))
    file_path = base_path / f'{filename}.{extension}'
    if file_path.exists():
        raise RuntimeError(f'Operation cancelled - path {file_path} already exists.')
    with open(file_path, 'wb') as f:
        f.write(random_bytes)


def _make_dummy_folder(base_path: Path | str, folder_name: str):
    if not isinstance(base_path, Path):
        base_path = Path(base_path)
    if not base_path.exists():
        raise RuntimeError(f'path {base_path} doesn\'t exist!')
    if not isinstance(folder_name, str):
        raise TypeError('[folder_name] parameter must be a str object.')

    dir_to_create = base_path / folder_name
    dir_to_create.mkdir(parents=True, exist_ok=True)
