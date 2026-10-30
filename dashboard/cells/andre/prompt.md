# Cell prompt — André Silva

> A race between four tiny neural networks learning a painting by Maria
> Helena Vieira da Silva from scratch, in the browser: a plain ReLU MLP,
> SIREN, Fourier features and a multiresolution hash grid (Instant-NGP).
> Each network maps a pixel's position (x, y) to its colour.
>
> Make the race fair and say so:
> - Same theoretical capacity: exactly 8,707 trainable float32 parameters
>   each (MLP 2→64→64→64→3; SIREN the same with ω₀=30; 67 random Fourier
>   features → 64 → 64 → 3; hash grid 8 levels × 504 entries × 2 → 32 → 3).
>   Check the counts at startup and print the check in the log.
> - Same compute: each network trains in its own Web Worker and gets exactly
>   the same CPU time.
> - Same painting: alternate *Bibliothèque* (1949) and *L'arène* (1950), one
>   minute per race. Each network's hyperparameters are tuned so none is
>   handicapped.
>
> Show it like a real training run for a computer-science audience: the
> target next to each network's live guess with its PSNR, a leaderboard that
> reorders (log overtakes), PSNR curves, and a `tail -f train.log` with the
> model summaries and per-network step, loss, PSNR, learning rate, gradient
> norm and it/s. End each race with the winner's snapshots next to the
> target, while the lanes alternate between each network's final guess and
> its error map. In the small grid tile, show only the leader and one live
> line.
>
> Caption at the bottom: "This is a race between four tiny neural networks
> with the same theoretical capacity learning the same painting with the
> same compute.", with a smaller line underneath saying each has exactly
> 8,707 trainable numbers and the same CPU time. The top bar shows the
> painting's title, her name and the year. Green-on-black, matching the
> dashboard theme. Link to my homepage (andre15silva.github.io).
