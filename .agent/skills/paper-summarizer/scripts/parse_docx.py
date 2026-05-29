import sys
import os
import docx

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from docx.table import Table
from docx.text.paragraph import Paragraph

def extract_docx_ordered(docx_path):
    if not os.path.exists(docx_path):
        print(f"Error: File '{docx_path}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        doc = docx.Document(docx_path)
        output = []

        # Traverse document XML body elements to extract paragraphs and tables in order
        for child in doc.element.body:
            # Paragraph element (tag: w:p)
            if child.tag.endswith('p'):
                p = Paragraph(child, doc)
                text = p.text.strip()
                if text:
                    output.append(text)
            
            # Table element (tag: w:tbl)
            elif child.tag.endswith('tbl'):
                t = Table(child, doc)
                table_rows = []
                for row in t.rows:
                    # Extract text from cells, cleaning newlines
                    row_cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
                    
                    # De-duplicate adjacent cell texts caused by merged cells in python-docx
                    clean_row_cells = []
                    for cell in row_cells:
                        if not clean_row_cells or clean_row_cells[-1] != cell:
                            clean_row_cells.append(cell)
                    
                    if clean_row_cells:
                        table_rows.append(" | ".join(clean_row_cells))
                
                if table_rows:
                    output.append("\n[Table]\n" + "\n".join(table_rows) + "\n[/Table]\n")

        return "\n\n".join(output)
    except Exception as e:
        print(f"Error parsing DOCX: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_docx.py <path_to_docx>")
        sys.exit(1)

    docx_file = sys.argv[1]
    parsed_text = extract_docx_ordered(docx_file)
    print(parsed_text)
