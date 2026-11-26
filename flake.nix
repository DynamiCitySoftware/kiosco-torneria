{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      python = pkgs.python3.withPackages (ps: [ ps.pyqt6 ps.pytest ps.pyserial ]);
    in {
      devShells.${system}.default = pkgs.mkShell {
        packages = [
          python
          pkgs.ugs
        ];
        shellHook = ''
          export PYTHONPATH="$PWD/src:$PYTHONPATH"
          alias ui-plato='PYTHONPATH=src KIOSCO=0 python3 -c "from pathlib import Path; from PyQt6.QtWidgets import QApplication; import sys; from centros_de_trabajo.ui.plato.ui_plato import VentanaPlato; app=QApplication(sys.argv); w=VentanaPlato(Path('"'"'src/centros_de_trabajo/estaciones/plato/programas'"'"')); w.showNormal(); sys.exit(app.exec())"'
        '';
      };

      #nixosModules.default = import ./nix/module.nix;
    };
}