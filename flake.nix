{
  description = "snatch game images";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
  };

  outputs = inputs@{ self, nixpkgs, flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      systems = [ "x86_64-linux" "aarch64-linux" ];

      perSystem = { config, self', inputs', pkgs, system, ... }: {
        _module.args.pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };

        devShells.default = let
          python-packages = p: with p; [ requests vdf loguru ];
          python-with-packages = pkgs.python311.withPackages (python-packages);
        in pkgs.mkShell {
          buildInputs = with pkgs; [ python-with-packages steamcmd ];

          shellHook = ''
            echo "Welcome to the development environment!"
          '';
        };
      };
    };
}
