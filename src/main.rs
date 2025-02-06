use std::env::consts::OS;

fn main() {
    if OS != "linux" {
        panic!("This program is only available on Linux");
    }
}
