import os

def print_tree(root, prefix=''):
    entries = sorted(os.listdir(root))
    for index, name in enumerate(entries):
        path = os.path.join(root, name)
        connector = '└── ' if index == len(entries) - 1 else '├── '
        print(prefix + connector + name)
        if os.path.isdir(path):
            extension = '    ' if index == len(entries) - 1 else '│   '
            print_tree(path, prefix + extension)

if __name__ == '__main__':
    # Ajusta esta ruta a tu carpeta Dissertation en OneDrive
    base_dir = '/Users/danielaresendiz/Library/CloudStorage/OneDrive-UniversityCollegeLondon(2)/Dissertation'
    print(base_dir)
    print_tree(base_dir)
