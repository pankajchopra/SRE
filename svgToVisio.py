import win32com.client


def convert_svg_to_visio(svg_path, output_path):
    try:
        # Create a Visio application instance
        visio_app = win32com.client.Dispatch("Visio.Application")

        # Set Visio app to be visible
        visio_app.Visible = True

        # Create a new document
        visio_doc = visio_app.Documents.Add("")

        # Import SVG to Visio
        page = visio_doc.Pages.Add()  # Add a new page to the document
        shape = page.Import(svg_path)

        # Save the document as a Visio file (.vsdx)
        visio_doc.SaveAs(output_path)

        # Close the document
        visio_doc.Close()

        # Quit the Visio application
        visio_app.Quit()

        print(f"Successfully converted '{svg_path}' to '{output_path}'.")
    except Exception as e:
        print(f"An error occurred: {e}")


# Example usage:
svg_file = r"Untitled.svg"
output_visio = r"Untitled.vsdx"
convert_svg_to_visio(svg_file, output_visio)
