import 'package:flutter/material.dart';
import 'book_reader_screen.dart';

class CoverScreen extends StatelessWidget {
  const CoverScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF3D342B),
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            final isMobile = constraints.maxWidth < 700;

            if (isMobile) {
              return _buildMobileLayout(context);
            }

            return _buildDesktopLayout(context);
          },
        ),
      ),
    );
  }

  // ============================================================
  // DESKTOP / TABLET LAYOUT
  // ============================================================

  Widget _buildDesktopLayout(BuildContext context) {
    return Row(
      children: [
        // --------------------------------------------------------
        // LEFT SIDE — COVER
        // --------------------------------------------------------
        Expanded(
          child: Container(
            color: const Color(0xFF3D342B),
            child: Column(
              children: [
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.all(30),
                    child: Center(
                      child: Image.asset(
                        "assets/images/cover.png",
                        fit: BoxFit.contain,
                      ),
                    ),
                  ),
                ),

                Padding(
                  padding: const EdgeInsets.only(bottom: 35),
                  child: _buildBeginButton(context),
                ),
              ],
            ),
          ),
        ),

        // --------------------------------------------------------
        // RIGHT SIDE — DESCRIPTION
        // --------------------------------------------------------
        Expanded(
          child: Container(
            color: const Color(0xFFF3E6C8),
            child: Center(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(50),
                child: _buildDescription(),
              ),
            ),
          ),
        ),
      ],
    );
  }

  // ============================================================
  // MOBILE LAYOUT
  // ============================================================

  Widget _buildMobileLayout(BuildContext context) {
    return SingleChildScrollView(
      child: Column(
        children: [
          // ------------------------------------------------------
          // COVER SECTION
          // ------------------------------------------------------
          Container(
            width: double.infinity,
            color: const Color(0xFF3D342B),
            child: Column(
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(25, 25, 25, 20),
                  child: Image.asset(
                    "assets/images/cover.png",
                    fit: BoxFit.contain,
                  ),
                ),

                Padding(
                  padding: const EdgeInsets.only(bottom: 30),
                  child: _buildBeginButton(context),
                ),
              ],
            ),
          ),

          // ------------------------------------------------------
          // DESCRIPTION SECTION
          // ------------------------------------------------------
          Container(
            width: double.infinity,
            color: const Color(0xFFF3E6C8),
            padding: const EdgeInsets.all(30),
            child: _buildDescription(),
          ),
        ],
      ),
    );
  }

  // ============================================================
  // BEGIN READING BUTTON
  // ============================================================

  Widget _buildBeginButton(BuildContext context) {
    return SizedBox(
      width: 290,
      height: 58,
      child: ElevatedButton(
        onPressed: () {
          Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const BookReaderScreen()),
          );
        },
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF6B8E23),
          foregroundColor: Colors.white,
          elevation: 4,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(30),
          ),
        ),
        child: const Text(
          "Begin Reading",
          style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
        ),
      ),
    );
  }

  // ============================================================
  // BOOK DESCRIPTION
  // ============================================================

  Widget _buildDescription() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: const [
        Text(
          "The Magic Picture",
          style: TextStyle(
            color: Color(0xFF5A4030),
            fontSize: 28,
            fontWeight: FontWeight.bold,
          ),
        ),

        SizedBox(height: 10),

        Text(
          "About the Series",
          style: TextStyle(
            color: Color(0xFF6B8E23),
            fontSize: 21,
            fontWeight: FontWeight.w600,
          ),
        ),

        SizedBox(height: 22),

        Text(
          "The Magic Picture is part of our "
          "Get Set Go Series, where we introduce "
          "children to the basics of technology "
          "and cybersecurity through engaging "
          "stories and memorable characters.\n\n"
          "Each story explores an important "
          "digital-life lesson in a simple, "
          "age-appropriate way, helping children "
          "build good technology and online-safety "
          "habits from an early age.",
          style: TextStyle(color: Color(0xFF5A4030), fontSize: 18, height: 1.6),
        ),
      ],
    );
  }
}
