{
  description = "";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };

  outputs =
    {
      self,
      nixpkgs,
      ...
    }:
    let
      supportedSystems = [
        "x86_64-linux"
        "aarch64-linux"
      ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
      pkgsFor = forAllSystems (system: import nixpkgs { inherit system; });
      lib = nixpkgs.lib;
    in
    {
      packages = forAllSystems (
        system:
        let
          pkgs = pkgsFor.${system};

          mkSystemdUnit =
            name: type: config:
            assert lib.lists.any (x: x == type) [
              "service"
              "timer"
              "path"
            ];
            pkgs.writeText "${name}.${type}"
              (nixpkgs.lib.nixosSystem {
                system = "${system}";
                modules = [ { systemd."${type}s".${name} = config; } ];
              }).config.systemd.units."${name}.${type}".text;

          mkSystemdUserUnit =
            name: type: config:
            pkgs.writeShellScriptBin "activate" ''
              set -euo pipefail
              export XDG_RUNTIME_DIR="/run/user/$UID"
              loginctl enable-linger "$USER"
              #mkdir -p "$HOME/.config/systemd/user" "$HOME/.config/systemd/user/default.target.wants"
              rm -f -- "$HOME/.config/systemd/user/${name}.${type}" #"$HOME/.config/systemd/user/default.target.wants/${name}.${type}"
              ln -s ${mkSystemdUnit name type config} "$HOME/.config/systemd/user/${name}.${type}"
              #ln -s "$HOME/.config/systemd/user/${name}.${type}" "$HOME/.config/systemd/user/default.target.wants"
              systemctl --user daemon-reload
              systemctl --user enable ${name}.${type}
              systemctl --user restart ${name}.${type}
            '';

        in
        {
          default = derivation; # should run the activate script for the service and timer

          script = pkgs.writers.writePython3Bin "dscovr" {
            libraries = [
              pkgs.python3Packages.opencv4
              pkgs.python3Packages.numpy
              pkgs.python3Packages.pillow
            ];
            doCheck = false;
          } "${builtins.readFile ./dscovr.py}";

          timer = mkSystemdUserUnit "dscovr-nix" "timer" {
            description = "running dscovr every 10 minutes";
            wantedBy = [ "timers.target" ];
            timerConfig = {
              Unit = "dscovr-nix.service";
              OnActiveSec = "20s";
              OnUnitActiveSec = "10m";
            };
          };

          service = mkSystemdUserUnit "dscovr-nix" "service" {
            description = "dscovr python script";
            wants = [ "dscovr-nix.timer" ];
            wantedBy = [ "default.target" ];
            serviceConfig = {
              ExecStart = "${self.packages."${system}".script}/bin/dscovr -o %h/.cache/dscovr -n 10 -b %h/.local/share/dscovr/dscovr_background.png -c";
            };
          };
        }
      );

      #devShells = forAllSystems (
      #  system:
      #  let
      #  in
      #  {
      #    default = ""
      #  }
      #);
    };
}
