from mplsoccer import Pitch, VerticalPitch, FontManager, Sbopen
import matplotlib.pyplot as plt

def plot_map(map_stats, res, significant = False):
    # Plotting
    result = list(map_stats.values())[0]
    if significant:
        result['statistic'] = res[1]
    else:
        result['statistic'] = res[0]

    pitch = Pitch(pitch_type='opta', line_zorder=4,
                  pitch_color='#22312b', line_color='#efefef')
    # draw
    fig, ax = pitch.draw(figsize=(6.6, 4.125))
    fig.set_facecolor('#22312b')
    pcm = pitch.heatmap(result, ax=ax, cmap='hot', edgecolors='#22312b')#, vmax = 0.01)
    # Add the colorbar and format off-white
    cbar = fig.colorbar(pcm, ax=ax, shrink=0.6)
    cbar.outline.set_edgecolor('#efefef')
    cbar.ax.yaxis.set_tick_params(color='#efefef')
    ticks = plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='#efefef')
    return fig

def plot_heatmap_general (map_stats):
    data = list(map_stats.values())[0]
    pitch = Pitch(pitch_type='opta', line_zorder=4,
                pitch_color='#22312b', line_color='#efefef')
    fig, ax = pitch.draw(figsize=(6.6, 4.125))
    fig.set_facecolor('#22312b')
    pcm = pitch.heatmap(data, ax=ax, cmap='hot', edgecolors='#22312b')#, vmax = 0.01)
    # Add the colorbar and format off-white
    cbar = fig.colorbar(pcm, ax=ax, shrink=0.6)
    cbar.outline.set_edgecolor('#efefef')
    cbar.ax.yaxis.set_tick_params(color='#efefef')
    ticks = plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='#efefef')
    return fig
