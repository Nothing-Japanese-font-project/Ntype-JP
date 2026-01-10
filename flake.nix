{
  description = "Ntype-JP development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          uv
          python313
        ];

        shellHook = ''
          echo "Welcome to Ntype-JP development environment (via Flake 25.05)!"
          echo "Using uv for Python environment management (Python 3.13)."
        '';
      };
    };
}
