import 'dart:async';

import 'package:flutter/material.dart';

import '../models/story_page_model.dart';
import '../models/story_data.dart';
import '../services/audio_service.dart';
import 'cover_screen.dart';

class StoryScreen extends StatefulWidget {
  final int pageIndex;

  const StoryScreen({super.key, required this.pageIndex});

  @override
  State<StoryScreen> createState() => _StoryScreenState();
}

class _StoryScreenState extends State<StoryScreen> {
  final AudioService _audioService = AudioService();

  static final Set<int> bookmarkedPages = {};

  late final StreamSubscription<bool> _audioStateSubscription;

  bool _isPlaying = false;

  @override
  void initState() {
    super.initState();

    _audioStateSubscription = _audioService.isPlayingStream.listen((isPlaying) {
      if (!mounted) return;

      setState(() {
        _isPlaying = isPlaying;
      });
    });
  }

  @override
  void dispose() {
    _audioStateSubscription.cancel();
    _audioService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final page = magicPictureStory[widget.pageIndex];

    return Scaffold(
      backgroundColor: const Color(0xFF342B24),

      // ------------------------------------------------------------
      // TOP BAR
      // ------------------------------------------------------------
      appBar: AppBar(
        backgroundColor: const Color(0xFF3A332B),
        elevation: 0,
        centerTitle: true,

        leading: IconButton(
          tooltip: "Home",
          icon: const Icon(Icons.home_rounded, color: Color(0xFFF3E6C8)),
          onPressed: () {
            _audioService.stop();

            Navigator.pushAndRemoveUntil(
              context,
              MaterialPageRoute(builder: (_) => const CoverScreen()),
              (route) => false,
            );
          },
        ),

        title: Text(
          "${page.pageNumber}/${magicPictureStory.length}",
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.w600,
            fontSize: 18,
          ),
        ),

        actions: [
          IconButton(
            tooltip: "Bookmark",
            icon: Icon(
              bookmarkedPages.contains(page.pageNumber)
                  ? Icons.bookmark
                  : Icons.bookmark_border,
              color: const Color(0xFFF3E6C8),
            ),
            onPressed: () {
              setState(() {
                if (bookmarkedPages.contains(page.pageNumber)) {
                  bookmarkedPages.remove(page.pageNumber);
                } else {
                  bookmarkedPages.add(page.pageNumber);
                }
              });
            },
          ),
        ],
      ),

      // ------------------------------------------------------------
      // MAIN CONTENT
      // ------------------------------------------------------------
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 12),

          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 850),

              child: Column(
                children: [
                  // ==================================================
                  // BOOK / IMAGE AREA
                  // ==================================================
                  Expanded(
                    child: LayoutBuilder(
                      builder: (context, constraints) {
                        // Keep the book page from becoming excessively
                        // tall on phones while still allowing it to grow
                        // on larger screens.
                        final double bookHeight = constraints.maxHeight.clamp(
                          560.0,
                          900.0,
                        );
                        final bool isDesktop = constraints.maxWidth >= 700;

                        final String imagePath = isDesktop
                            ? page.image.replaceFirst(
                                RegExp(r'\.png$'),
                                '_landscape.png',
                              )
                            : page.image;

                        return Center(
                          child: SizedBox(
                            height: bookHeight,
                            width: double.infinity,

                            child: Container(
                              padding: const EdgeInsets.all(10),

                              decoration: BoxDecoration(
                                color: const Color(0xFFF3E6C8),

                                borderRadius: BorderRadius.circular(32),

                                border: Border.all(
                                  color: const Color(0xFFD8B978),
                                  width: 2,
                                ),

                                boxShadow: const [
                                  BoxShadow(
                                    color: Color(0x66452F22),
                                    blurRadius: 18,
                                    spreadRadius: 2,
                                    offset: Offset(0, 8),
                                  ),
                                ],
                              ),

                              child: Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 18,
                                  vertical: 18,
                                ),

                                decoration: BoxDecoration(
                                  color: const Color(0xFFF3E6C8),

                                  borderRadius: BorderRadius.circular(24),

                                  border: Border.all(
                                    color: const Color(0xFFE9D7B4),
                                    width: 1.2,
                                  ),
                                ),

                                // ------------------------------------------------
                                // IMAGE
                                // ------------------------------------------------
                                child: Center(
                                  child: ClipRRect(
                                    borderRadius: BorderRadius.circular(18),
                                    child: Image.asset(
                                      imagePath,
                                      fit: BoxFit.contain,
                                      width: double.infinity,
                                      height: double.infinity,
                                    ),
                                  ),
                                ),
                              ),
                            ),
                          ),
                        );
                      },
                    ),
                  ),

                  const SizedBox(height: 18),

                  // ==================================================
                  // NAVIGATION BUTTONS
                  // ==================================================
                  Row(
                    children: [
                      // ------------------------------------------------
                      // PREVIOUS
                      // ------------------------------------------------
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: widget.pageIndex > 0
                              ? () {
                                  Navigator.pushReplacement(
                                    context,
                                    MaterialPageRoute(
                                      builder: (_) => StoryScreen(
                                        pageIndex: widget.pageIndex - 1,
                                      ),
                                    ),
                                  );
                                }
                              : null,

                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFFF3E6C8),

                            foregroundColor: const Color(0xFF5A4030),

                            disabledBackgroundColor: const Color(0xFFD8C8A8),

                            disabledForegroundColor: const Color(0xFF9B8B72),

                            elevation: 2,

                            side: const BorderSide(
                              color: Color(0xFFD8B978),
                              width: 1,
                            ),

                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(22),
                            ),

                            padding: const EdgeInsets.symmetric(vertical: 12),
                          ),

                          icon: const Icon(Icons.arrow_back),

                          label: const Text("Previous"),
                        ),
                      ),

                      const SizedBox(width: 10),

                      // ------------------------------------------------
                      // READ TO ME
                      // ------------------------------------------------
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: () async {
                            if (_isPlaying) {
                              await _audioService.stop();
                            } else {
                              await _audioService.playPageAudio(
                                widget.pageIndex + 1,
                              );
                            }
                          },

                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFFF3E6C8),

                            foregroundColor: const Color(0xFF5A4030),

                            elevation: 2,

                            side: const BorderSide(
                              color: Color(0xFFD8B978),
                              width: 1,
                            ),

                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(22),
                            ),

                            padding: const EdgeInsets.symmetric(vertical: 12),
                          ),

                          icon: Icon(
                            _isPlaying
                                ? Icons.volume_off_rounded
                                : Icons.volume_up_rounded,
                          ),

                          label: Text(
                            _isPlaying ? "Stop Reading" : "Read to Me",
                          ),
                        ),
                      ),

                      const SizedBox(width: 10),

                      // ------------------------------------------------
                      // NEXT
                      // ------------------------------------------------
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed:
                              widget.pageIndex < magicPictureStory.length - 1
                              ? () {
                                  Navigator.pushReplacement(
                                    context,
                                    MaterialPageRoute(
                                      builder: (_) => StoryScreen(
                                        pageIndex: widget.pageIndex + 1,
                                      ),
                                    ),
                                  );
                                }
                              : null,

                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFFF3E6C8),

                            foregroundColor: const Color(0xFF5A4030),

                            disabledBackgroundColor: const Color(0xFFD8C8A8),

                            disabledForegroundColor: const Color(0xFF9B8B72),

                            elevation: 2,

                            side: const BorderSide(
                              color: Color(0xFFD8B978),
                              width: 1,
                            ),

                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(22),
                            ),

                            padding: const EdgeInsets.symmetric(vertical: 12),
                          ),

                          icon: const Icon(Icons.arrow_forward),

                          label: const Text("Next"),
                        ),
                      ),
                    ],
                  ),

                  const SizedBox(height: 4),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
