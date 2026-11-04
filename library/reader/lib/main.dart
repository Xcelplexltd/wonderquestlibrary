import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:audioplayers/audioplayers.dart';
import 'package:web/web.dart' as web;

class StoryBook {
  final String id, title, imageRoot, audioRoot;
  final int pageCount;
  const StoryBook(this.id, this.title, this.pageCount, this.imageRoot, this.audioRoot);
  String image(int page, bool landscape) => '$imageRoot/story_${(page + 1).toString().padLeft(2, '0')}${landscape ? '_landscape' : ''}.webp';
  String audio(int page) => '$audioRoot/page${(page + 1).toString().padLeft(2, '0')}.mp3';
}
const books = {'magic-picture': StoryBook('magic-picture', 'The Magic Picture', 13, 'assets/images', 'audio')};
void main() {
  final id = Uri.base.queryParameters['book'] ?? 'magic-picture';
  runApp(MaterialApp(debugShowCheckedModeBanner: false, title: 'GetSetGo Story Reader', theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xff527059)), useMaterial3: true), home: books[id] == null ? const MissingBook() : Reader(book: books[id]!)));
}
void goHome() => web.window.location.assign('../#books');
class MissingBook extends StatelessWidget {
  const MissingBook({super.key});
  @override Widget build(BuildContext context) => Scaffold(body: Center(child: Column(mainAxisSize: MainAxisSize.min, children: [const Text('This book is not on our shelf yet.'), TextButton(onPressed: goHome, child: const Text('Back to the bookshelf'))])));
}
class Reader extends StatefulWidget {
  final StoryBook book;
  const Reader({super.key, required this.book});
  @override State<Reader> createState() => _ReaderState();
}
class _ReaderState extends State<Reader> {
  final AudioPlayer player = AudioPlayer();
  StreamSubscription<PlayerState>? subscription;
  int page = 0;
  int? bookmark;
  bool playing = false, loading = false;
  int audioRequest = 0;
  String? audioError;
  String get key => 'getsetgo.${widget.book.id}';
  String? read(String suffix) { try { return web.window.localStorage.getItem('$key.$suffix'); } catch (_) { return null; } }
  void save(String suffix, String? value) { try { if (value == null) { web.window.localStorage.removeItem('$key.$suffix'); } else { web.window.localStorage.setItem('$key.$suffix', value); } } catch (_) {} }
  @override void initState() {
    super.initState();
    page = (int.tryParse(read('page') ?? '') ?? 0).clamp(0, widget.book.pageCount - 1);
    final stored = int.tryParse(read('bookmark') ?? '');
    bookmark = stored != null && stored >= 0 && stored < widget.book.pageCount ? stored : null;
    subscription = player.onPlayerStateChanged.listen((state) { if (mounted) setState(() => playing = state == PlayerState.playing); });
  }
  Future<void> turn(int next) async {
    if (next < 0 || next >= widget.book.pageCount) return;
    audioRequest++;
    setState(() { page = next; playing = false; loading = false; audioError = null; });
    save('page', '$page');
    await player.stop();
  }
  Future<void> toggleAudio() async {
    if (loading) return;
    final request = ++audioRequest;
    if (playing) { await player.stop(); return; }
    setState(() { loading = true; audioError = null; });
    try {
      await player.play(AssetSource(widget.book.audio(page))).timeout(const Duration(seconds: 20));
      if (request != audioRequest) await player.stop();
    } catch (_) { if (mounted && request == audioRequest) setState(() => audioError = 'The narration could not load. Please try again.'); }
    finally { if (mounted && request == audioRequest) setState(() => loading = false); }
  }
  @override void dispose() { subscription?.cancel(); player.dispose(); super.dispose(); }
  @override Widget build(BuildContext context) {
    final book = widget.book;
    return CallbackShortcuts(bindings: {const SingleActivator(LogicalKeyboardKey.arrowRight): () { turn(page + 1); }, const SingleActivator(LogicalKeyboardKey.arrowLeft): () { turn(page - 1); }}, child: Focus(autofocus: true, child: Scaffold(
      backgroundColor: const Color(0xfffaf7ed),
      appBar: AppBar(backgroundColor: const Color(0xffe4eadc), leading: IconButton(tooltip: 'Back to bookshelf', onPressed: goHome, icon: const Icon(Icons.home_outlined)), title: Text(book.title, style: const TextStyle(fontFamily: 'Georgia', fontSize: 20)), actions: [IconButton(tooltip: bookmark == page ? 'Remove bookmark' : 'Bookmark this page', onPressed: () { setState(() => bookmark = bookmark == page ? null : page); save('bookmark', bookmark?.toString()); }, icon: Icon(bookmark == page ? Icons.bookmark : Icons.bookmark_border)), if (bookmark != null) IconButton(tooltip: 'Go to bookmarked page', onPressed: () { turn(bookmark!); }, icon: const Icon(Icons.bookmarks_outlined))]),
      body: SafeArea(child: Column(children: [Padding(padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16), child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [Text('Page ${page + 1} of ${book.pageCount}', style: const TextStyle(color: Color(0xff52674c))), const SizedBox(width: 18), TextButton(onPressed: page == 0 ? null : () { turn(0); }, child: const Text('Start again'))])),
        Expanded(child: LayoutBuilder(builder: (context, box) { final landscape = box.maxWidth > box.maxHeight; return Padding(padding: const EdgeInsets.symmetric(horizontal: 12), child: Center(child: InteractiveViewer(minScale: 1, maxScale: 3, key: ValueKey(page), child: Image.asset(book.image(page, landscape), fit: BoxFit.contain, width: box.maxWidth, height: box.maxHeight, semanticLabel: '${book.title}, page ${page + 1}. Use Read to Me for narration.', errorBuilder: (_, error, stack) => const Center(child: Text('This page could not load. Please refresh the reader.')))))); })),
        if (audioError != null) Padding(padding: const EdgeInsets.all(6), child: Text(audioError!, textAlign: TextAlign.center, style: const TextStyle(color: Colors.red))),
        Padding(padding: const EdgeInsets.fromLTRB(12, 12, 12, 8), child: Wrap(alignment: WrapAlignment.center, spacing: 12, runSpacing: 8, children: [OutlinedButton.icon(onPressed: page > 0 ? () { turn(page - 1); } : null, icon: const Icon(Icons.chevron_left), label: const Text('Previous')), FilledButton.icon(onPressed: loading ? null : toggleAudio, icon: Icon(playing ? Icons.stop_rounded : Icons.volume_up_outlined), label: Text(loading ? 'Loading…' : playing ? 'Stop reading' : 'Read to Me')), OutlinedButton.icon(onPressed: page < book.pageCount - 1 ? () { turn(page + 1); } : null, icon: const Icon(Icons.chevron_right), label: const Text('Next'))])),
        Padding(padding: const EdgeInsets.only(bottom: 8), child: Text(page == book.pageCount - 1 ? 'The end • What did you discover?' : 'Read at your own pace • Pinch to zoom', style: const TextStyle(fontSize: 11, color: Color(0xff687561))))
      ])),
    )));
  }
}
