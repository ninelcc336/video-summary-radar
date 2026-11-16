"""验证可读目录、身份复用和本地文件身份。"""
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from prepare_output import prepare_output


def test_identity_survives_title_change_and_keeps_human_files(tmp_path):
    """同视频改标题仍复用目录，不动已有稿件；分 P 独立。"""
    first = prepare_output(tmp_path, '标题:测试?/演示', 'bilibili', 'BV123', part='1')
    assert first.name == '标题_测试__演示__bilibili-BV123-p1'
    (first / '口播稿.txt').write_text('人类修改', encoding='utf-8')
    assert prepare_output(tmp_path, '完全不同的标题', 'bilibili', 'BV123', part='1') == first
    assert (first / '口播稿.txt').read_text(encoding='utf-8') == '人类修改'
    assert prepare_output(tmp_path, '标题', 'bilibili', 'BV123', part='2') != first
    assert not (first / '视频总结.md').exists()


def test_local_file_rename_reuses_content_identity(tmp_path):
    """文件改名不产生重复视频，内容改变才形成新的身份。"""
    source = tmp_path / 'a.mp4'
    source.write_bytes(b'video bytes')
    command = [sys.executable, str(SCRIPTS / 'prepare_output.py'), '--title', '本地视频',
               '--local-file', str(source), '--output-root', str(tmp_path / 'outputs')]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    first = json.loads(result.stdout)['directory']
    renamed = tmp_path / 'b.mp4'
    source.rename(renamed)
    command[command.index(str(source))] = str(renamed)
    second = subprocess.run(command, capture_output=True, text=True)
    assert json.loads(second.stdout)['directory'] == first
    renamed.write_bytes(b'changed video bytes')
    changed = subprocess.run(command, capture_output=True, text=True)
    assert json.loads(changed.stdout)['directory'] != first
