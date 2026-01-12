#!/usr/bin/env python3
"""Interactive quote cleanup tool."""

import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any, Optional

from rapidfuzz import fuzz, process

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_FILE = PROJECT_ROOT / "data" / "processed" / "quotes_cleaned.json"
BACKUP_FILE = PROJECT_ROOT / "data" / "processed" / "quotes_cleaned.backup.json"


class QuoteCleanup:
    """Interactive quote cleanup manager."""

    def __init__(self):
        self.quotes: list[dict[str, Any]] = []
        self.load_quotes()
        self.modified = False

    def load_quotes(self):
        """Load quotes from JSON file."""
        if not DATA_FILE.exists():
            print(f"✗ Error: {DATA_FILE} not found")
            exit(1)

        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            self.quotes = json.load(f)
        print(f"✓ Loaded {len(self.quotes)} quotes from {DATA_FILE}")

    def save_quotes(self):
        """Save quotes with backup."""
        # Create backup
        if DATA_FILE.exists():
            shutil.copy2(DATA_FILE, BACKUP_FILE)
            print(f"✓ Backup saved to {BACKUP_FILE}")

        # Save updated quotes
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.quotes, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved {len(self.quotes)} quotes to {DATA_FILE}")
        self.modified = False

    def get_author_stats(self) -> dict[str, int]:
        """Get author frequency counts."""
        return Counter(q.get('author', 'Unknown') for q in self.quotes)

    def display_quote_detailed(self, quote: dict, index: int, total: int, show_original: bool = False):
        """Enhanced quote display with all fields and optional original values."""
        print("\n" + "=" * 80)
        print(f"Quote {index + 1}/{total}")
        print("=" * 80)

        author = quote.get('author', 'Unknown')
        text = quote.get('quote', '')
        context = quote.get('context') or '[No context]'
        source = quote.get('source') or '[No source]'

        print(f"\nAuthor:  {author}")
        print(f"Quote:   {text}")
        print(f"Context: {context}")
        print(f"Source:  {source}")

        if show_original and '_original' in quote:
            orig = quote['_original']
            print("\n--- Original Values ---")
            if orig.get('author') != author:
                print(f"Author:  {orig.get('author', 'Unknown')}")
            if orig.get('quote') != text:
                print(f"Quote:   {orig.get('quote', '')[:80]}...")
            if orig.get('context') != quote.get('context'):
                print(f"Context: {orig.get('context') or '[No context]'}")

        print("=" * 80)

    def get_all_authors_ranked(self) -> list[tuple[str, int]]:
        """Get all authors sorted by frequency (most common first)."""
        stats = self.get_author_stats()
        return sorted(stats.items(), key=lambda x: (-x[1], x[0]))

    def fuzzy_match_author(self, query: str, authors: list[tuple[str, int]]) -> Optional[str]:
        """Fuzzy match author name, show suggestions if no exact match."""
        # Exact match (case-insensitive)
        for author, _ in authors:
            if author.lower() == query.lower():
                return author

        # Fuzzy match
        author_names = [a for a, _ in authors]
        matches = process.extract(
            query,
            author_names,
            scorer=fuzz.token_sort_ratio,
            limit=5,
            score_cutoff=60
        )

        if matches:
            print("\nDid you mean:")
            for i, (name, score, _) in enumerate(matches, 1):
                print(f"  {i}. {name} ({score}% match)")
            print(f"  {len(matches) + 1}. Use '{query}' as new author")
            print("  0. Cancel")

            choice = input("Select: ").strip()
            if choice.isdigit():
                idx = int(choice)
                if idx == 0:
                    return None
                elif 1 <= idx <= len(matches):
                    return matches[idx - 1][0]
                elif idx == len(matches) + 1:
                    return query.title()

        # No matches, create new
        confirm = input(f"Create new author '{query.title()}'? [y/N]: ").strip().lower()
        if confirm == 'y':
            return query.title()

        return None

    def display_author_picker(self, current_author: Optional[str] = None) -> Optional[str]:
        """Interactive author picker with frequency display."""
        authors = self.get_all_authors_ranked()

        print("\n" + "=" * 60)
        print("Author Selection")
        print("=" * 60)
        print("Type author name or select from list:")
        print()

        # Show top 20 authors with numbers
        print("Top Authors:")
        for i, (author, count) in enumerate(authors[:20], 1):
            marker = " *" if author == current_author else ""
            print(f"  {i:2d}. {author:30s} ({count:3d} quotes){marker}")

        if len(authors) > 20:
            print(f"\n  ... and {len(authors) - 20} more authors")

        print("\nOptions:")
        print("  - Type number (1-20) to select from list")
        print("  - Type author name to search/create new")
        print("  - Press Enter to keep current author")
        print("  - Type 'cancel' to abort")
        print()

        choice = input("Author: ").strip()

        # Handle numeric selection
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < min(20, len(authors)):
                return authors[idx][0]

        # Handle cancel
        if choice.lower() == 'cancel':
            return None

        # Handle empty (keep current)
        if not choice:
            return current_author

        # Handle fuzzy search for typed name
        return self.fuzzy_match_author(choice, authors)

    def delete_by_author(self):
        """Delete all quotes by a specific author."""
        stats = self.get_author_stats()
        print("\nTop authors:")
        for author, count in stats.most_common(20):
            print(f"  {author}: {count}")

        author_name = input("\nEnter author name to delete (or 'cancel'): ").strip()
        if not author_name or author_name.lower() == 'cancel':
            return

        matching_quotes = [q for q in self.quotes if q.get('author') == author_name]
        if not matching_quotes:
            print(f"✗ No quotes found by '{author_name}'")
            return

        print(f"\nFound {len(matching_quotes)} quotes by '{author_name}'")
        print("Sample quotes:")
        for q in matching_quotes[:3]:
            quote_text = q.get('quote', '')[:80]
            print(f"  - {quote_text}...")

        confirm = input(f"\nDelete all {len(matching_quotes)} quotes? [y/N]: ").strip().lower()
        if confirm == 'y':
            self.quotes = [q for q in self.quotes if q.get('author') != author_name]
            print(f"✓ Deleted {len(matching_quotes)} quotes ({len(self.quotes)} remaining)")
            self.modified = True
            self.save_quotes()

    def delete_unknown(self):
        """Delete all Unknown quotes."""
        unknown_quotes = [q for q in self.quotes if q.get('author') == 'Unknown']
        if not unknown_quotes:
            print("✓ No Unknown quotes found")
            return

        print(f"\nFound {len(unknown_quotes)} Unknown quotes")
        print("Sample quotes:")
        for q in unknown_quotes[:5]:
            quote_text = q.get('quote', '')[:80]
            print(f"  - {quote_text}...")

        confirm = input(f"\nDelete all {len(unknown_quotes)} Unknown quotes? [y/N]: ").strip().lower()
        if confirm == 'y':
            self.quotes = [q for q in self.quotes if q.get('author') != 'Unknown']
            print(f"✓ Deleted {len(unknown_quotes)} quotes ({len(self.quotes)} remaining)")
            self.modified = True
            self.save_quotes()

    def delete_short_quotes(self):
        """Delete quotes shorter than N words."""
        min_words_str = input("\nMinimum words (default 5): ").strip()
        min_words = int(min_words_str) if min_words_str else 5

        short_quotes = [q for q in self.quotes if len(q.get('quote', '').split()) < min_words]
        if not short_quotes:
            print(f"✓ No quotes shorter than {min_words} words")
            return

        print(f"\nFound {len(short_quotes)} quotes shorter than {min_words} words")
        print("Sample quotes:")
        for q in short_quotes[:5]:
            quote_text = q.get('quote', '')
            author = q.get('author', 'Unknown')
            print(f"  - \"{quote_text}\" - {author}")

        confirm = input(f"\nDelete all {len(short_quotes)} short quotes? [y/N]: ").strip().lower()
        if confirm == 'y':
            self.quotes = [q for q in self.quotes if len(q.get('quote', '').split()) >= min_words]
            print(f"✓ Deleted {len(short_quotes)} quotes ({len(self.quotes)} remaining)")
            self.modified = True
            self.save_quotes()

    def find_duplicate_authors(self) -> list[tuple[list[str], int]]:
        """Find similar author names using fuzzy matching."""
        stats = self.get_author_stats()
        authors = list(stats.keys())

        # Group similar authors
        groups: dict[str, list[str]] = {}
        processed = set()

        for author in authors:
            if author in processed:
                continue

            # Find similar authors (80%+ similarity)
            matches = process.extract(
                author,
                [a for a in authors if a not in processed],
                scorer=fuzz.token_sort_ratio,
                limit=10,
                score_cutoff=80
            )

            if len(matches) > 1:
                similar_authors = [m[0] for m in matches]
                groups[author] = similar_authors
                processed.update(similar_authors)

        # Return groups with total quote count
        return [
            (group, sum(stats[a] for a in group))
            for group in groups.values()
            if len(group) > 1
        ]

    def merge_authors(self):
        """Merge duplicate authors."""
        print("\nFinding duplicate authors...")
        duplicate_groups = self.find_duplicate_authors()

        if not duplicate_groups:
            print("✓ No duplicate authors found")
            return

        print(f"\nFound {len(duplicate_groups)} author groups with duplicates:\n")
        for i, (group, total_count) in enumerate(duplicate_groups, 1):
            stats = self.get_author_stats()
            counts = [f"{author} ({stats[author]})" for author in group]
            print(f"{i}. {' + '.join(counts)} = {total_count} total quotes")

        confirm = input(f"\nMerge these {len(duplicate_groups)} author groups? [y/N]: ").strip().lower()
        if confirm != 'y':
            return

        # Process each group
        merged_count = 0
        for group, _ in duplicate_groups:
            # Choose canonical name (longest one or most common)
            stats = self.get_author_stats()
            canonical = max(group, key=lambda a: (stats[a], len(a)))

            # Merge all to canonical
            for author in group:
                if author != canonical:
                    for quote in self.quotes:
                        if quote.get('author') == author:
                            quote['author'] = canonical
                    merged_count += 1

        print(f"✓ Merged {merged_count} duplicate authors into {len(duplicate_groups)} canonical names")
        self.modified = True
        self.save_quotes()

    def edit_quote_multifield(self, quote: dict):
        """Multi-field editor submenu."""
        while True:
            print("\n" + "-" * 60)
            print("Edit Quote Fields")
            print("-" * 60)
            print(f"1. Author:  {quote.get('author', 'Unknown')}")
            print(f"2. Quote:   {quote.get('quote', '')[:60]}...")
            print(f"3. Context: {quote.get('context') or '[None]'}")
            print(f"4. Source:  {quote.get('source') or '[None]'}")
            print("5. Done (save changes)")
            print("0. Cancel (discard changes)")
            print("-" * 60)

            choice = input("Edit field (0-5): ").strip()

            if choice == '1':
                new_author = self.display_author_picker(quote.get('author'))
                if new_author:
                    quote['author'] = new_author
                    print(f"✓ Updated author")
            elif choice == '2':
                print(f"\nCurrent: {quote.get('quote', '')}")
                new_text = input("New quote text: ").strip()
                if new_text:
                    quote['quote'] = new_text
                    print("✓ Updated quote")
            elif choice == '3':
                print(f"\nCurrent: {quote.get('context') or '[None]'}")
                new_context = input("New context: ").strip()
                quote['context'] = new_context if new_context else None
                print("✓ Updated context")
            elif choice == '4':
                print(f"\nCurrent: {quote.get('source') or '[None]'}")
                new_source = input("New source: ").strip()
                quote['source'] = new_source if new_source else None
                print("✓ Updated source")
            elif choice == '5':
                print("✓ Changes saved")
                break
            elif choice == '0':
                # Restore original
                if '_original' in quote:
                    quote.update(quote['_original'])
                print("✓ Changes discarded")
                break

    def manual_review_enhanced(self, filter_unknown: bool = False):
        """Enhanced manual review with multi-field editing and author picker."""
        # Filter for Unknown authors if requested
        quotes_to_review = self.quotes
        if filter_unknown:
            quotes_to_review = [q for q in self.quotes if q.get('author') == 'Unknown']
            print(f"\nFiltering {len(quotes_to_review)} Unknown quotes for review")

        if not quotes_to_review:
            print("No quotes to review!")
            return

        print("\nEnhanced Manual Review Mode")
        print("Commands: [K]eep, [D]elete, [E]dit, [A]uthor, [Q]uote, [C]ontext, [S]ource, [N]ext, [P]rev, [U]it")

        i = 0
        deleted_indices = []

        while i < len(quotes_to_review):
            quote = quotes_to_review[i]

            # Store original for comparison if not already stored
            if '_original' not in quote:
                quote['_original'] = {
                    'author': quote.get('author'),
                    'quote': quote.get('quote'),
                    'context': quote.get('context'),
                    'source': quote.get('source')
                }

            # Display quote
            has_changes = quote != quote.get('_original', {})
            self.display_quote_detailed(quote, i, len(quotes_to_review), show_original=has_changes)

            action = input("\nAction [k/d/e/a/q/c/s/n/p/u]: ").strip().lower()

            if action == 'd':
                # Delete quote
                deleted_indices.append(i)
                print(f"✓ Marked for deletion")
                i += 1

            elif action == 'e':
                # Multi-field edit menu
                self.edit_quote_multifield(quote)
                self.modified = True

            elif action == 'a':
                # Quick author edit with picker
                new_author = self.display_author_picker(quote.get('author'))
                if new_author:
                    quote['author'] = new_author
                    print(f"✓ Updated author to '{new_author}'")
                    self.modified = True
                i += 1

            elif action == 'q':
                # Quick quote text edit
                print(f"\nCurrent: {quote.get('quote', '')}")
                new_text = input("New quote text (or Enter to cancel): ").strip()
                if new_text:
                    quote['quote'] = new_text
                    print("✓ Updated quote text")
                    self.modified = True
                i += 1

            elif action == 'c':
                # Quick context edit
                print(f"\nCurrent: {quote.get('context') or '[None]'}")
                new_context = input("New context (or Enter to clear): ").strip()
                quote['context'] = new_context if new_context else None
                print("✓ Updated context")
                self.modified = True
                i += 1

            elif action == 's':
                # Quick source edit
                print(f"\nCurrent: {quote.get('source') or '[None]'}")
                new_source = input("New source (or Enter to clear): ").strip()
                quote['source'] = new_source if new_source else None
                print("✓ Updated source")
                self.modified = True
                i += 1

            elif action == 'p':
                # Previous quote
                i = max(0, i - 1)

            elif action == 'n':
                # Next quote (skip)
                i += 1

            elif action == 'u' or action == 'quit':
                # Quit review
                break

            else:  # Default: keep and move to next
                i += 1

        # Remove deleted quotes
        if deleted_indices:
            # Remove in reverse order to maintain indices
            for idx in sorted(deleted_indices, reverse=True):
                self.quotes.remove(quotes_to_review[idx])
            print(f"\n✓ Deleted {len(deleted_indices)} quotes")
            self.modified = True

        # Remove _original markers
        for quote in self.quotes:
            if '_original' in quote:
                del quote['_original']

        if self.modified:
            self.save_quotes()

    def manual_review(self):
        """Manual review mode - browse and edit quotes."""
        print("\nManual review mode")
        print("Commands: [K]eep, [D]elete, [E]dit author, [Q]uit")

        i = 0
        deleted_count = 0

        while i < len(self.quotes):
            quote = self.quotes[i]
            author = quote.get('author', 'Unknown')
            quote_text = quote.get('quote', '')

            print("\n" + "=" * 80)
            print(f"Quote {i+1}/{len(self.quotes)}")
            print(f"Author: {author}")
            print(f"Quote: {quote_text}")
            print("=" * 80)

            action = input("Action [K/d/e/q]: ").strip().lower()

            if action == 'd':
                del self.quotes[i]
                deleted_count += 1
                print(f"✓ Deleted ({len(self.quotes)} remaining)")
            elif action == 'e':
                new_author = input("New author name: ").strip()
                if new_author:
                    quote['author'] = new_author
                    print(f"✓ Updated author to '{new_author}'")
                    self.modified = True
                i += 1
            elif action == 'q':
                break
            else:  # keep or any other input
                i += 1

        if deleted_count > 0 or self.modified:
            print(f"\n✓ Deleted {deleted_count} quotes in manual review")
            self.modified = True
            self.save_quotes()

    def add_new_quote(self):
        """Add a new quote interactively."""
        print("\n" + "=" * 60)
        print("Add New Quote")
        print("=" * 60)

        # Get quote text
        print("\nEnter quote text (required):")
        quote_text = input("> ").strip()
        if not quote_text:
            print("✗ Quote text is required")
            return

        # Get author with picker
        print("\nSelect or enter author:")
        author = self.display_author_picker()
        if not author:
            print("✗ Author is required")
            return

        # Get optional context
        print("\nEnter context (optional, press Enter to skip):")
        context = input("> ").strip()

        # Get optional source
        print("\nEnter source (optional, press Enter to skip):")
        source = input("> ").strip()

        # Confirm
        print("\n" + "-" * 60)
        print("Preview:")
        print(f"Author:  {author}")
        print(f"Quote:   {quote_text}")
        print(f"Context: {context or '[None]'}")
        print(f"Source:  {source or '[None]'}")
        print("-" * 60)

        confirm = input("\nAdd this quote? [y/N]: ").strip().lower()
        if confirm == 'y':
            new_quote = {
                'author': author,
                'quote': quote_text,
                'context': context if context else None,
                'source': source if source else None
            }
            self.quotes.append(new_quote)
            self.modified = True
            print(f"✓ Added quote ({len(self.quotes)} total)")
            self.save_quotes()
        else:
            print("✗ Cancelled")

    def show_stats(self):
        """Show current statistics."""
        stats = self.get_author_stats()
        print(f"\n{'=' * 60}")
        print(f"Current Statistics")
        print(f"{'=' * 60}")
        print(f"Total quotes: {len(self.quotes)}")
        print(f"Unique authors: {len(stats)}")
        print(f"\nTop 15 authors:")
        for author, count in stats.most_common(15):
            print(f"  {author}: {count}")
        print(f"{'=' * 60}")

    def run(self):
        """Run interactive cleanup menu."""
        while True:
            self.show_stats()

            print("\n" + "=" * 60)
            print("Quote Cleanup Menu")
            print("=" * 60)
            print("[1] Delete by author name")
            print("[2] Delete Unknown quotes")
            print("[3] Delete short quotes")
            print("[4] Merge duplicate authors")
            print("[5] Manual review mode (all quotes)")
            print("[6] Fix Unknown authors")
            print("[7] Add new quote")
            print("[8] Save and exit")
            print("[q] Exit without saving")
            print("=" * 60)

            choice = input("\nChoose: ").strip().lower()

            if choice == '1':
                self.delete_by_author()
            elif choice == '2':
                self.delete_unknown()
            elif choice == '3':
                self.delete_short_quotes()
            elif choice == '4':
                self.merge_authors()
            elif choice == '5':
                self.manual_review_enhanced(filter_unknown=False)
            elif choice == '6':
                self.manual_review_enhanced(filter_unknown=True)
            elif choice == '7':
                self.add_new_quote()
            elif choice == '8':
                if self.modified:
                    self.save_quotes()
                print("\n✓ Cleanup complete!")
                print(f"Final count: {len(self.quotes)} quotes")
                print("\nNext steps:")
                print("  1. Run: python backend/app/scripts/reingest_cleaned_quotes.py")
                print("  2. Restart: docker-compose up")
                break
            elif choice == 'q':
                if self.modified:
                    confirm = input("Exit without saving changes? [y/N]: ").strip().lower()
                    if confirm != 'y':
                        continue
                print("✓ Exited without saving")
                break
            else:
                print("Invalid choice")


def main():
    """Main entry point."""
    cleanup = QuoteCleanup()
    cleanup.run()


if __name__ == "__main__":
    main()
