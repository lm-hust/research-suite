import sys
import os
import pdfplumber

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def extract_layout_aware_text(pdf_path):
    if not os.path.exists(pdf_path):
        print(f"Error: File '{pdf_path}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = []
            for page in pdf.pages:
                full_text.append(f"\n--- Page {page.page_number} ---\n")
                
                # Retrieve all words on the page with their bounding boxes
                words = page.extract_words(x_tolerance=3, y_tolerance=3)
                if not words:
                    # Fallback to basic text extraction if no words are found
                    text = page.extract_text()
                    if text:
                        full_text.append(text)
                    continue

                width = page.width
                height = page.height
                mid = width / 2

                # Detect if the page layout is multi-column or single column.
                # We divide the page vertically into left and right columns.
                # If we see a high overlap of vertical ranges with words distinctively on
                # the left and right sides, we treat it as double column.
                left_y_ranges = []
                right_y_ranges = []
                for w in words:
                    # Ignore header/footer margins (top 40pt, bottom 40pt)
                    if w['top'] < 40 or w['bottom'] > height - 40:
                        continue
                    if w['x1'] <= mid - 5:
                        left_y_ranges.append((w['top'], w['bottom']))
                    elif w['x0'] >= mid + 5:
                        right_y_ranges.append((w['top'], w['bottom']))

                # Determine double column region
                # If there are substantial words in both columns, we extract them column-wise
                if len(left_y_ranges) > 20 and len(right_y_ranges) > 20:
                    # Extract single-column header (e.g. Title, Abstract)
                    # Find where double-column section starts. A simple heuristic:
                    # The first y-coordinate where left and right column text both appear.
                    min_left_y = min(y[0] for y in left_y_ranges) if left_y_ranges else 0
                    min_right_y = min(y[0] for y in right_y_ranges) if right_y_ranges else 0
                    split_y = max(min_left_y, min_right_y) - 10 # Allow some margin

                    # If the split coordinate is below the top margin
                    if split_y > 50:
                        # Extract header (single column)
                        header_bbox = (0, 0, width, split_y)
                        header_crop = page.crop(header_bbox)
                        header_text = header_crop.extract_text()
                        if header_text:
                            full_text.append(header_text)
                            full_text.append("\n")
                    else:
                        split_y = 0

                    # Extract columns (double column region)
                    left_bbox = (0, split_y, mid, height)
                    right_bbox = (mid, split_y, width, height)

                    left_crop = page.crop(left_bbox)
                    right_crop = page.crop(right_bbox)

                    left_text = left_crop.extract_text()
                    right_text = right_crop.extract_text()

                    if left_text:
                        full_text.append(left_text)
                        full_text.append("\n")
                    if right_text:
                        full_text.append(right_text)
                        full_text.append("\n")
                else:
                    # Default: Single column extraction
                    text = page.extract_text()
                    if text:
                        full_text.append(text)
            
            return "".join(full_text)
    except Exception as e:
        print(f"Error parsing PDF: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_pdf.py <path_to_pdf>")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    parsed_text = extract_layout_aware_text(pdf_file)
    print(parsed_text)
