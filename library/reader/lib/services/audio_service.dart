import 'package:audioplayers/audioplayers.dart';

class AudioService {
  final AudioPlayer _player = AudioPlayer();

  Stream<bool> get isPlayingStream =>
      _player.onPlayerStateChanged.map((state) => state == PlayerState.playing);

  Future<void> playPageAudio(int pageNumber) async {
    await _player.stop();

    final fileName = 'audio/page${pageNumber.toString().padLeft(2, '0')}.mp3';

    await _player.play(AssetSource(fileName));
  }

  Future<void> stop() async {
    await _player.stop();
  }

  Future<void> dispose() async {
    await _player.dispose();
  }
}
