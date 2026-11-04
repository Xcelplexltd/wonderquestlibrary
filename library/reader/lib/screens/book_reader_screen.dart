import 'package:flutter/material.dart';
import 'story_screen.dart';

class BookReaderScreen extends StatefulWidget {
  const BookReaderScreen({super.key});

  @override
  State<BookReaderScreen> createState() => _BookReaderScreenState();
}

class _BookReaderScreenState extends State<BookReaderScreen> {
  int currentPage = 0;

  @override
  Widget build(BuildContext context) {
    return StoryScreen(pageIndex: currentPage);
  }
}
